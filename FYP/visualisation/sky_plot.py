import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import defaultdict
from models.beam_model import BeamModel
from core.observer import Observer
import logging
log = logging.getLogger(__name__)

class SkyPlot:
    """
    Dual animated hemisphere projection:
    Left: full sky view with absolute target track
    Right: target-centred relative view with gain-coloured satellite positions
    """
    def __init__(self, beam_model: BeamModel, observer: Observer, results: list):
        self.beam_model = beam_model
        self.observer = observer
        self.results = results
        self.plot_radius = beam_model.prefilter_radius_deg * 1.5
        self.gain_cutoff_percent = beam_model.threshold * 100
        self._organise_by_time()
        self._prepare_target_track()

    def _organise_by_time(self):
        """
        Organise results by timestamp
        """
        self.by_time = defaultdict(list)
        for row in self.results:
            # normalise +00:00 to Z to match skyfield utc_iso() format
            key = row["time_utc"].replace('+00:00', 'Z')
            self.by_time[key].append(row)
        self.sorted_times = [t.utc_iso() for t in self.observer.time_array]

    def _prepare_target_track(self):
        """
        Pull full precomputed target track from observer for the absolute sky plot.
        Converts skyfield time array to ISO strings for frame lookup.
        """
        self.full_target_alts = self.observer.target_alts
        self.full_target_azs  = self.observer.target_azs
        #altitude for polar plot: 90 at zenith, 0 at horizon
        self.full_target_r    = self.full_target_alts
        self.full_target_theta = np.radians(self.full_target_azs)

    def _to_polar_relative(self, sat_az, sat_alt, target_az, target_alt):
        """
        Convert satellite position to polar coordinates relative to target.
        theta = relative azimuth, r = angular separation in degrees.
        """
        theta = np.radians(sat_az) - np.radians(target_az)
        alt1, az1, alt2, az2 = map(np.radians, [target_alt, target_az, sat_alt, sat_az])
        d_az = az2 - az1
        cos_sep = (np.sin(alt1) * np.sin(alt2) + np.cos(alt1) * np.cos(alt2) * np.cos(d_az))
        r = np.degrees(np.arccos(np.clip(cos_sep, -1, 1)))
        return theta, r

    def animate(self, save_path=None, progress_callback=None):
        """
        Renders dual animated hemisphere projection.
        Optionally saves to file if save_path is provided.
        """
        fig = plt.figure(figsize=(16, 8))
        fig.patch.set_facecolor('#1a1a2e')

        #Left plot: full sky absolute
        #----------------------------
        ax_sky = fig.add_subplot(121, polar=True)
        ax_sky.set_facecolor('#1a1a2e')
        ax_sky.set_theta_zero_location('N')
        ax_sky.set_theta_direction(-1)
        ax_sky.set_rlim(90, 0)
        ax_sky.set_rlabel_position(135)
        ax_sky.set_title("Full Sky View", pad=20, color='white')
        ax_sky.tick_params(colors='white')

        # full target track as faint trail
        ax_sky.plot(self.full_target_theta, self.full_target_r,
                    color='white', alpha=0.2, linewidth=1, label='Target track')

        # current target position marker — updated per frame
        target_marker_sky, = ax_sky.plot([], [], 'g*', markersize=10, label='Target')

        # satellite scatter for full sky
        sat_scatter_sky = ax_sky.scatter([], [], c=[], cmap='plasma',
                                          vmin=0, vmax=100, s=40, zorder=5)

        ax_sky.legend(loc='lower left', fontsize=8, labelcolor='white',
                      facecolor='#1a1a2e', edgecolor='white')
        #----------------------------
        #Right plot: target-centred relative
        #----------------------------
        ax_rel = fig.add_subplot(122, polar=True)
        ax_rel.set_facecolor('#1a1a2e')
        ax_rel.set_theta_zero_location('N')
        ax_rel.set_theta_direction(-1)
        ax_rel.set_rlim(0, self.plot_radius)
        ax_rel.set_rlabel_position(135)
        ax_rel.set_title("Beam View — Target Centred", pad=20, color='white')
        ax_rel.tick_params(colors='white')

        boundary_theta = np.linspace(0, 2 * np.pi, 360)

        # prefilter boundary
        ax_rel.plot(boundary_theta,
                    np.full_like(boundary_theta, self.beam_model.prefilter_radius_deg),
                    color='blue', linestyle='--', linewidth=1,
                    label=f'Prefilter ({self.beam_model.prefilter_radius_deg:.2f}°)')

        # gain cutoff circle
        ax_rel.plot(boundary_theta,
                    np.full_like(boundary_theta, self.beam_model.prefilter_radius_deg / 1.5),
                    color='red', linestyle=':', linewidth=1,
                    label=f'{self.gain_cutoff_percent}% gain threshold')

        # target locked at centre
        ax_rel.plot(0, 0, 'g*', markersize=12, label='Target')

        sat_scatter_rel = ax_rel.scatter([], [], c=[], cmap='plasma',
                                          vmin=0, vmax=100, s=40, zorder=5)

        ax_rel.legend(loc='lower left', fontsize=8, labelcolor='white',
                      facecolor='#1a1a2e', edgecolor='white')

        annotations = []
        time_text = fig.text(0.5, 0.02, '', ha='center', fontsize=10, color='white')

        #frame index lookup for target track
        #map each result timestamp to nearest index in full time array
        time_tt = self.observer.time_array.tt

        def get_track_index(iso_time_str):
            #parse ISO string back to skyfield tt for nearest lookup
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(iso_time_str).replace(tzinfo=timezone.utc)
            t = self.observer.ts.from_datetime(dt)
            return int(np.argmin(np.abs(time_tt - t.tt)))
        
        #----------------------------

        def update(frame):
            nonlocal annotations
            for ann in annotations:
                ann.remove()
            annotations = []

            time_key = self.sorted_times[frame]
            rows = self.by_time[time_key]

            #update target marker on full sky plot
            idx = get_track_index(time_key)
            target_marker_sky.set_data(
                [self.full_target_theta[idx]],
                [self.full_target_r[idx]]
            )
            
            ann = ax_rel.annotate(
                f'Alt {self.full_target_alts[idx]:.1f}°  Az {self.full_target_azs[idx]:.1f}°',
                xy=(0, 0),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=7,
                color='lightgreen'
            )
            annotations.append(ann)

            #satellite positions
            thetas_rel, rs_rel, gains = [], [], []
            thetas_sky, rs_sky = [], []

            for row in rows:
                #relative plot
                theta_r, r_r = self._to_polar_relative(
                    row["sat_az_deg"], row["sat_alt_deg"],
                    row["target_az_deg"], row["target_alt_deg"]
                )
                if r_r <= self.plot_radius:
                    thetas_rel.append(theta_r)
                    rs_rel.append(r_r)
                    gains.append(row["gain_percent"])

                    ann = ax_rel.annotate(
                        row["satellite"],
                        xy=(theta_r, r_r),
                        xytext=(5, 5),
                        textcoords='offset points',
                        fontsize=7,
                        color='white'
                    )
                    annotations.append(ann)

                #absolute sky plot
                thetas_sky.append(np.radians(row["sat_az_deg"]))
                rs_sky.append(row["sat_alt_deg"])

            #update relative scatter
            if thetas_rel:
                sat_scatter_rel.set_offsets(np.c_[thetas_rel, rs_rel])
                sat_scatter_rel.set_array(np.array(gains))
            else:
                sat_scatter_rel.set_offsets(np.empty((0, 2)))
                sat_scatter_rel.set_array(np.array([]))

            #update sky scatter
            if thetas_sky:
                sat_scatter_sky.set_offsets(np.c_[thetas_sky, rs_sky])
                sat_scatter_sky.set_array(np.array(gains))
            else:
                sat_scatter_sky.set_offsets(np.empty((0, 2)))
                sat_scatter_sky.set_array(np.array([]))

            time_text.set_text(f'UTC: {time_key}')
            return [sat_scatter_rel, sat_scatter_sky, target_marker_sky, time_text] + annotations

        anim = animation.FuncAnimation(
            fig,
            update,
            frames=len(self.sorted_times),
            interval=200,
            blit=False
        )

        plt.tight_layout()

        if save_path:
            anim.save(save_path, writer='ffmpeg', fps=10, dpi=150, 
                  progress_callback=progress_callback)
            log.info(f"Animation saved to {save_path}")
        else:
            plt.show()