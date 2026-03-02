"""
Secuencia_2Robots_V01.py
Ejecución separada del scheduler dinámico (código aparte).
No modifica ni integra el flujo de Comunicacion_RoboDk_V01.py.
"""

from OperationScheduler import DynamicCycleController, Operation
from csv_loader import OperationConfigLoader


def main() -> None:
    print("=" * 70)
    print("SECUENCIA 2 ROBOTS - MODO APARTE")
    print("Scheduler dinamico independiente del script principal")
    print("=" * 70)

    loader = OperationConfigLoader()
    configs = loader.load_from_csv("operations_config.csv")

    if not configs:
        print("[ERR] No se pudo cargar operations_config.csv")
        return

    controller = DynamicCycleController(max_cycles=2)

    for key in sorted(configs.keys()):
        cfg = configs[key]
        op_name = f"{cfg.operation_name}_{cfg.robot}"

        op = Operation(
            name=op_name,
            robot=cfg.robot,
            frames={"primary": cfg.frames[0] if cfg.frames else "frame"},
            speeds={
                "linear_mm_s": cfg.speeds_linear_mm_s,
                "joint_deg_s": cfg.speeds_joint_deg_s,
            },
            work_time_s=cfg.work_time_s,
            priority=cfg.priority,
            passes=cfg.passes,
            input_parts_needed=cfg.input_parts,
            output_parts_generated=cfg.output_parts,
            requires_r2_free=cfg.requires_r2_free,
        )

        controller.add_operation_to_queue(op)
        controller.add_part_buffer(f"{op.name}_input", initial_parts=5)
        controller.add_part_buffer(f"{op.name}_output", initial_parts=0)

    def callback_execute(op: Operation) -> None:
        print(f"[RUN] {op.name} -> {op.robot}")

    controller.run_all_cycles(callback_execute=callback_execute)
    print("[DONE] Secuencia aparte finalizada")


if __name__ == "__main__":
    main()
