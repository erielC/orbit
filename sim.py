import uuid
import matplotlib
from dotenv import load_dotenv
import os

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rocketpy import Environment, SolidMotor, Rocket, Flight

load_dotenv()

PRESETS = {
    "simulate": {"name": "base simulation", "mass": 15, "inclination": 90},
    "simulate SpaceX rocket": {
        "name": "Falcon 9 Rocket",
        "mass": 14.426,
        "inclination": 84,
    },
    "simulate heavy rocket": {"name": "Heavy Rocket", "mass": 20.0, "inclination": 75},
    "simulate model rocket": {"name": "Model Rocket", "mass": 8.0, "inclination": 88},
}


# Cesaroni L1395 thrust curve (time in s, thrust in N)
L1395_THRUST = [
    (0.0, 0.0),
    (0.1, 1530.0),
    (0.3, 1590.0),
    (0.7, 1560.0),
    (1.2, 1520.0),
    (1.8, 1500.0),
    (2.4, 1490.0),
    (3.0, 1480.0),
    (3.5, 1460.0),
    (3.9, 1440.0),
    (4.0, 0.0),
]


def run_simulation(preset_key: str = "1") -> dict:
    p = PRESETS[preset_key]

    env = Environment(latitude=41.775, longitude=-86.572, elevation=236)

    motor = SolidMotor(
        thrust_source=L1395_THRUST,
        burn_time=4.0,
        dry_mass=2.952,
        dry_inertia=(0, 0, 0),
        center_of_dry_mass_position=0.397,
        grains_center_of_mass_position=0.397,
        grain_number=5,
        grain_separation=0.005,
        grain_density=1750,
        grain_outer_radius=0.033,
        grain_initial_inner_radius=0.015,
        grain_initial_height=0.12,
        nozzle_radius=0.033,
        throat_radius=0.011,
        interpolation_method="linear",
        nozzle_position=0.0,
        coordinate_system_orientation="combustion_chamber_to_nozzle",
    )

    rocket = Rocket(
        radius=0.0635,
        mass=p["mass"],
        inertia=(6.321, 6.321, 0.034),
        power_off_drag=0.43,
        power_on_drag=0.43,
        center_of_mass_without_motor=0.0,
        coordinate_system_orientation="nose_to_tail",
    )
    rocket.set_rail_buttons(1.5, 2, 45)
    rocket.add_motor(motor=motor, position=-1.373)
    rocket.add_nose(length=0.55829, kind="tangent", position=1.278)
    rocket.add_trapezoidal_fins(
        4, span=0.170, root_chord=0.270, tip_chord=0.090, position=-1.04
    )
    rocket.add_parachute(
        "Main", cd_s=10.0, trigger="apogee", sampling_rate=105, lag=1.5
    )

    flight = Flight(
        rocket=rocket,
        environment=env,
        rail_length=5.18,
        inclination=p["inclination"],
        heading=133,
    )

    apogee_m = flight.apogee - env.elevation
    apogee_ft = apogee_m * 3.28084

    filename = f"orbit_sim.png"
    plot_path = f"assets/{filename}"

    fig, axs = plt.subplots(3, 1, figsize=(8, 10))

    # Altitude
    t = flight.z[:, 0]
    alt = flight.z[:, 1] - env.elevation

    axs[0].plot(t, alt, linewidth=2)
    axs[0].set_title("Altitude vs Time")
    axs[0].set_xlabel("Time (s)")
    axs[0].set_ylabel("Altitude AGL (m)")
    axs[0].grid(True, alpha=0.3)

    # Velocity
    vt = flight.speed[:, 0]
    v = flight.speed[:, 1]

    axs[1].plot(vt, v, linewidth=2)
    axs[1].set_title("Velocity vs Time")
    axs[1].set_xlabel("Time (s)")
    axs[1].set_ylabel("Velocity (m/s)")
    axs[1].grid(True, alpha=0.3)

    # Mach
    mt = flight.mach_number[:, 0]
    mach = flight.mach_number[:, 1]

    axs[2].plot(mt, mach, linewidth=2)
    axs[2].set_title("Mach Number vs Time")
    axs[2].set_xlabel("Time (s)")
    axs[2].set_ylabel("Mach")
    axs[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()

    return {
        "name": p["name"],
        "apogee_ft": round(apogee_ft, 1),
        "apogee_m": round(apogee_m, 1),
        "max_velocity_ms": round(flight.max_speed, 1),
        "max_mach": round(flight.max_mach_number, 3),
        "time_to_apogee_s": round(flight.apogee_time, 1),
        "plot_url": f"https://orbitdemo.up.railway.app/assets/{filename}",
    }
