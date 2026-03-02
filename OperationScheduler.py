"""
OperationScheduler.py
Control dinámico de operaciones para R1/R2 según disponibilidad.
Reemplaza la secuencia fija por sistema flexible de colas.
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


class MachineStatus(Enum):
    """Estados de máquina."""
    IDLE = "IDLE"           # Libre, disponible
    BUSY = "BUSY"           # Ocupada ejecutando operación
    WAITING = "WAITING"     # Esperando recurso (ej: R2 espera a R1)
    ERROR = "ERROR"         # Error durante ejecución


@dataclass
class Operation:
    """Define una operación a ejecutar."""
    name: str                          # Ej: 'Op_10', 'Op_20'
    robot: str                         # 'R1' o 'R2'
    frames: Dict[str, str]             # {'frame': 'R1_Op_20', 'target_afuera': 'R1_Op_20_Pos_Afuera', ...}
    speeds: Dict[str, float]           # {'linear_mm_s': 500, 'joint_deg_s': 350, ...}
    work_time_s: float = 1.0          # Tiempo de trabajo (procesamiento) en segundos
    dwell_s: float = 0.0              # Pausa al final
    requires_r2_free: bool = False    # Si True, espera a que R2 esté libre
    priority: int = 0                 # Mayor número = más prioridad
    required_items_missing: List[str] = field(default_factory=list)  # Items faltantes
    passes: int = 1                   # Cuántas veces ejecutar esta op en un ciclo
    input_parts_needed: int = 1       # Cuántas piezas requiere como entrada
    output_parts_generated: int = 1   # Cuántas piezas genera como salida


@dataclass
class MachineState:
    """Estado actual de una máquina."""
    name: str                         # 'R1' o 'R2'
    status: MachineStatus = MachineStatus.IDLE
    current_operation: Optional[str] = None
    cycle_number: int = 0
    operations_completed: int = 0
    start_time: Optional[float] = None
    elapsed_time: float = 0.0

    def mark_busy(self, op_name: str) -> None:
        """Marca máquina como ocupada."""
        self.status = MachineStatus.BUSY
        self.current_operation = op_name
        self.start_time = time.time()

    def mark_idle(self) -> None:
        """Marca máquina como libre."""
        if self.start_time is not None:
            self.elapsed_time += time.time() - self.start_time
        self.status = MachineStatus.IDLE
        self.current_operation = None
        self.operations_completed += 1

    def mark_waiting(self, reason: str = "") -> None:
        """Marca máquina esperando."""
        self.status = MachineStatus.WAITING
        print(f"  [{self.name}] ESPERA: {reason}")

    def is_available(self) -> bool:
        """¿Está disponible para nueva operación?"""
        return self.status == MachineStatus.IDLE

    def __str__(self) -> str:
        op_str = self.current_operation or "-"
        return f"{self.name}[{self.status.value}] Op:{op_str} C:{self.cycle_number} Done:{self.operations_completed}"


@dataclass
class Part:
    """Representa una pieza en el sistema."""
    part_id: int
    created_at: float
    current_operation: Optional[str] = None
    completed_operations: List[str] = field(default_factory=list)
    status: str = "WAITING"  # WAITING, PROCESSING, DONE

    def __str__(self) -> str:
        return f"Pieza#{self.part_id} | Op:{self.current_operation} | Completadas:{len(self.completed_operations)}"


class PartBuffer:
    """Buffer de piezas entre operaciones."""

    def __init__(self, name: str, initial_parts: int = 0):
        self.name = name
        self.parts: List[Part] = [
            Part(part_id=i, created_at=time.time())
            for i in range(initial_parts)
        ]
        self.part_counter = initial_parts

    def add_parts(self, count: int) -> List[Part]:
        """Añade piezas al buffer."""
        new_parts = [
            Part(part_id=self.part_counter + i, created_at=time.time())
            for i in range(count)
        ]
        self.parts.extend(new_parts)
        self.part_counter += count
        print(f"    [BUFFER:{self.name}] +{count} piezas -> Total: {len(self.parts)}")
        return new_parts

    def take_parts(self, count: int) -> List[Part]:
        """Saca piezas del buffer."""
        if len(self.parts) < count:
            print(f"    [WARN] BUFFER:{self.name} - Insuficientes piezas ({len(self.parts)} < {count})")
            return []
        taken = self.parts[:count]
        self.parts = self.parts[count:]
        print(f"    [BUFFER:{self.name}] -{count} piezas -> Quedan: {len(self.parts)}")
        return taken

    def available_count(self) -> int:
        """Cuántas piezas hay disponibles."""
        return len(self.parts)

    def __str__(self) -> str:
        return f"{self.name}: {len(self.parts)} piezas"


class OperationQueue:
    """Gestiona cola de operaciones disponibles."""

    def __init__(self):
        self.operations: Dict[str, Operation] = {}
        self.executed_history: List[Tuple[str, str, float]] = []  # (op_name, robot, time_s)

    def add_operation(self, op: Operation) -> None:
        """Añade operación a la cola."""
        if not op.required_items_missing:
            self.operations[op.name] = op
            print(f"  [OK] Operacion {op.name} anadida (robot:{op.robot}, priority:{op.priority})")
        else:
            print(f"  [ERR] Operacion {op.name} OMITIDA (faltan items: {op.required_items_missing})")

    def get_available_operations(self, robot_name: str) -> List[str]:
        """Retorna operaciones disponibles para un robot específico, ordenadas por prioridad."""
        available = [
            op_name
            for op_name, op in self.operations.items()
            if op.robot == robot_name
        ]
        # Ordenar por prioridad (mayor primero)
        available.sort(
            key=lambda op_name: self.operations[op_name].priority,
            reverse=True
        )
        return available

    def select_next_operation(
        self,
        robot_name: str,
        machine_states: Dict[str, MachineState],
        skip_ops: List[str] = None
    ) -> Optional[Operation]:
        """
        Selecciona la mejor operación para un robot según:
        - Disponibilidad del robot
        - Restricciones (ej: requiere R2 libre)
        - Prioridad
        """
        if skip_ops is None:
            skip_ops = []

        available = self.get_available_operations(robot_name)

        for op_name in available:
            if op_name in skip_ops:
                continue

            op = self.operations[op_name]

            # Verificar restricciones
            if op.requires_r2_free:
                r2_state = machine_states.get('R2')
                if r2_state and not r2_state.is_available():
                    continue  # Saltar esta op si R2 no está libre

            return op

        return None

    def execute_operation(
        self,
        op: Operation,
        machine_states: Dict[str, MachineState],
        input_buffer: Optional[PartBuffer] = None,
        output_buffer: Optional[PartBuffer] = None,
        callback_execute: callable = None,
        callback_complete: callable = None
    ) -> float:
        """
        Ejecuta una operación (simula o ejecuta real con callback).
        Gestiona piezas de entrada/salida.
        Retorna tiempo transcurrido.
        """
        robot = machine_states[op.robot]
        robot.mark_busy(op.name)

        # Validar piezas de entrada
        input_parts = []
        if input_buffer:
            if input_buffer.available_count() < op.input_parts_needed:
                print(f"\n  [ERR] {op.name}: No hay suficientes piezas ({input_buffer.available_count()} < {op.input_parts_needed})")
                robot.mark_idle()
                return 0.0

            input_parts = input_buffer.take_parts(op.input_parts_needed)

        print(f"\n  EXEC: {op.name} en {op.robot}")
        print(f"    - Frames: {list(op.frames.keys())}")
        print(f"    - Velocidades: {op.speeds}")
        print(f"    - Tiempo trabajo: {op.work_time_s:.3f}s")
        if input_parts:
            print(f"    - Piezas entrada: {[str(p) for p in input_parts]}")

        start_t = time.time()

        # Si hay callback, lo ejecuta (ej: comunicación real con RoboDK)
        if callback_execute:
            try:
                callback_execute(op)
            except Exception as e:
                print(f"    [ERR] ERROR: {e}")
                robot.status = MachineStatus.ERROR
                return 0.0

        # Simular tiempo de trabajo
        time.sleep(op.work_time_s)

        # Simular dwell
        if op.dwell_s > 0:
            time.sleep(op.dwell_s)

        # Procesar piezas de salida
        if output_buffer and input_parts:
            output_parts = output_buffer.add_parts(op.output_parts_generated * len(input_parts))
            for part in input_parts:
                part.completed_operations.append(op.name)

        elapsed_t = time.time() - start_t
        robot.mark_idle()

        self.executed_history.append((op.name, op.robot, elapsed_t))

        if callback_complete:
            callback_complete(op, elapsed_t)

        print(f"    [OK] Completado en {elapsed_t:.3f}s")

        return elapsed_t


    def print_summary(self) -> None:
        """Resumen de ejecución."""
        print("\n=== RESUMEN OPERACIONES ===")
        for op_name, robot, elapsed_s in self.executed_history:
            print(f"  {op_name:15s} | {robot} | {elapsed_s:.3f}s")

        total_time = sum(t for _, _, t in self.executed_history)
        print(f"\nTIEMPO TOTAL: {total_time:.3f}s")


class DynamicCycleController:
    """Controlador dinámico de ciclos."""

    def __init__(self, max_cycles: int = 1):
        self.max_cycles = max_cycles
        self.queue = OperationQueue()
        self.machine_states: Dict[str, MachineState] = {
            'R1': MachineState('R1'),
            'R2': MachineState('R2'),
        }
        self.part_buffers: Dict[str, PartBuffer] = {}
        self.current_cycle = 0

    def add_operation_to_queue(self, op: Operation) -> None:
        """Añade operación a la cola."""
        self.queue.add_operation(op)

    def add_part_buffer(self, name: str, initial_parts: int = 0) -> PartBuffer:
        """Crea un buffer de piezas."""
        buffer = PartBuffer(name, initial_parts)
        self.part_buffers[name] = buffer
        return buffer

    def set_operation_work_time(self, op_name: str, work_time_s: float) -> None:
        """
        Modifica el tiempo de trabajo de una operación.
        Útil para ajustar según condiciones reales.
        """
        if op_name in self.queue.operations:
            self.queue.operations[op_name].work_time_s = work_time_s
            print(f"  [AJUSTE] {op_name}: tiempo de trabajo ajustado a {work_time_s:.3f}s")
        else:
            print(f"  [ERR] Operacion {op_name} no encontrada")

    def run_cycle(self, callback_execute: callable = None) -> bool:
        """
        Ejecuta un ciclo completo de operaciones.
        Retorna True si se ejecutó al menos una operación, False si termina.
        """
        self.current_cycle += 1
        print(f"\n{'='*60}")
        print(f"=== CICLO {self.current_cycle} ===")
        print(f"{'='*60}")

        for robot_name in ['R1', 'R2']:
            self.machine_states[robot_name].cycle_number = self.current_cycle

        # Mostrar estado de buffers
        print("\n[BUFFERS INICIALES]")
        for name, buffer in self.part_buffers.items():
            print(f"  {buffer}")

        ops_executed_this_cycle = 0
        skip_ops = []

        # Intentar ejecutar operaciones mientras haya disponibles
        while True:
            progress_made = False

            # Detectar qué máquinas están libres
            r1_available = self.machine_states['R1'].is_available()
            r2_available = self.machine_states['R2'].is_available()

            if not r1_available and not r2_available:
                print("\n  [INFO] Ambas máquinas ocupadas.")
                break

            # Seleccionar próxima operación para R1 si está libre
            if r1_available:
                next_op_r1 = self.queue.select_next_operation(
                    'R1',
                    self.machine_states,
                    skip_ops=skip_ops
                )

                if next_op_r1:
                    # Buscar buffers (ej: 'Op_10_input', 'Op_10_output')
                    input_buf = self.part_buffers.get(f"{next_op_r1.name}_input")
                    output_buf = self.part_buffers.get(f"{next_op_r1.name}_output")

                    elapsed = self.queue.execute_operation(
                        next_op_r1,
                        self.machine_states,
                        input_buffer=input_buf,
                        output_buffer=output_buf,
                        callback_execute=callback_execute
                    )
                    if elapsed > 0:
                        ops_executed_this_cycle += 1
                        progress_made = True

                    # Si la operación requiere múltiples pasadas, repetir
                    for pass_num in range(1, next_op_r1.passes):
                        print(f"\n  PASS {pass_num + 1}/{next_op_r1.passes}: {next_op_r1.name}")
                        elapsed_pass = self.queue.execute_operation(
                            next_op_r1,
                            self.machine_states,
                            input_buffer=input_buf,
                            output_buffer=output_buf,
                            callback_execute=callback_execute
                        )
                        if elapsed_pass > 0:
                            ops_executed_this_cycle += 1
                            progress_made = True
                else:
                    print(f"\n  [R1] No hay más operaciones disponibles en esta pasada.")
                    break

            # Seleccionar próxima operación para R2 si está libre
            if r2_available:
                next_op_r2 = self.queue.select_next_operation(
                    'R2',
                    self.machine_states,
                    skip_ops=skip_ops
                )

                if next_op_r2:
                    # Buscar buffers
                    input_buf = self.part_buffers.get(f"{next_op_r2.name}_input")
                    output_buf = self.part_buffers.get(f"{next_op_r2.name}_output")

                    elapsed = self.queue.execute_operation(
                        next_op_r2,
                        self.machine_states,
                        input_buffer=input_buf,
                        output_buffer=output_buf,
                        callback_execute=callback_execute
                    )
                    if elapsed > 0:
                        ops_executed_this_cycle += 1
                        progress_made = True

            if not progress_made:
                print("\n  [INFO] Sin progreso en esta iteracion, fin de ciclo para evitar bloqueo.")
                break

        print(f"\nCiclo {self.current_cycle}: {ops_executed_this_cycle} operaciones ejecutadas")
        print(f"  R1: {self.machine_states['R1']}")
        print(f"  R2: {self.machine_states['R2']}")

        # Mostrar estado final de buffers
        print("\n[BUFFERS FINALES]")
        for name, buffer in self.part_buffers.items():
            print(f"  {buffer}")

        return ops_executed_this_cycle > 0 and self.current_cycle < self.max_cycles

    def run_all_cycles(self, callback_execute: callable = None) -> None:
        """Ejecuta todos los ciclos."""
        while self.run_cycle(callback_execute=callback_execute):
            pass

        self.queue.print_summary()


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == '__main__':
    try:
        from csv_loader import OperationConfigLoader
        use_csv = True
    except ImportError:
        use_csv = False
        print("[WARN] csv_loader no disponible, usando configuracion manual")

    try:
        from operation_visualizer import OperationMetrics, GraphicalReport
        use_metrics = True
    except ImportError:
        use_metrics = False
        print("[WARN] operation_visualizer no disponible, metricas deshabilitadas")

    print("\n" + "="*70)
    print("OPERATION SCHEDULER v2.0")
    print("Control dinamico con CSV + tracking de piezas")
    print("="*70)

    controller = DynamicCycleController(max_cycles=2)

    if use_csv:
        print("\n[CSV] Cargando configuracion...")
        loader = OperationConfigLoader()
        csv_configs = loader.load_from_csv('operations_config.csv')

        if not csv_configs:
            raise Exception("No se pudieron cargar operaciones del CSV")

        for config_key in sorted(csv_configs.keys()):
            config = csv_configs[config_key]
            op_name = f"{config.operation_name}_{config.robot}"
            op = Operation(
                name=op_name,
                robot=config.robot,
                frames={'primary': config.frames[0] if config.frames else 'frame'},
                speeds={
                    'linear_mm_s': config.speeds_linear_mm_s,
                    'joint_deg_s': config.speeds_joint_deg_s,
                },
                work_time_s=config.work_time_s,
                priority=config.priority,
                passes=config.passes,
                input_parts_needed=config.input_parts,
                output_parts_generated=config.output_parts,
                requires_r2_free=config.requires_r2_free,
            )
            controller.add_operation_to_queue(op)
            controller.add_part_buffer(f"{op.name}_input", initial_parts=5)
            controller.add_part_buffer(f"{op.name}_output", initial_parts=0)
            print(f"  [OK] {op.name} cargada")
    else:
        print("\n[CONFIG] Carga manual")
        for op in [
            Operation('Op_10_R1', 'R1', {'frame': 'R1_Op_10'}, {'linear_mm_s': 500, 'joint_deg_s': 350}, work_time_s=1.5, priority=2, passes=2),
            Operation('Op_20_R1', 'R1', {'frame': 'R1_Op_20'}, {'linear_mm_s': 500, 'joint_deg_s': 350}, work_time_s=2.5, priority=3, passes=1),
            Operation('Op_70_R2', 'R2', {'frame': 'R2_Op_70'}, {'linear_mm_s': 500, 'joint_deg_s': 350}, work_time_s=2.0, priority=5, passes=1),
        ]:
            controller.add_operation_to_queue(op)
            controller.add_part_buffer(f"{op.name}_input", initial_parts=5)
            controller.add_part_buffer(f"{op.name}_output", initial_parts=0)

    metrics = OperationMetrics() if use_metrics else None
    if metrics:
        metrics.start_cycle()

    def execute_with_metrics(op: Operation):
        print(f"    [RUN] {op.name} en {op.robot}")
        if metrics:
            metrics.record_execution(
                op_name=op.name,
                robot=op.robot,
                parts_processed=op.output_parts_generated,
                success=True,
            )

    print("\n[START] Ejecutando ciclos...")
    controller.run_all_cycles(callback_execute=execute_with_metrics)

    if metrics:
        metrics.print_report()
        metrics.timeline_ascii()
        summary = metrics.get_summary()
        op_times = {op: info['total'] for op, info in summary['operation_times'].items()}
        GraphicalReport.bar_chart(op_times, "Tiempo total por operacion (s)")
        robot_times = {rb: info['total'] for rb, info in summary['robot_times'].items()}
        GraphicalReport.distribution_pie(robot_times, "Distribucion por robot")

    print("\n[DONE] Programa completado")

    # Crear controlador
    controller = DynamicCycleController(max_cycles=2)

    # Crear buffers de piezas
    entrada_op10 = controller.add_part_buffer('Op_10_input', initial_parts=5)
    salida_op10 = controller.add_part_buffer('Op_10_output', initial_parts=0)

    entrada_op20 = controller.add_part_buffer('Op_20_input', initial_parts=3)
    salida_op20 = controller.add_part_buffer('Op_20_output', initial_parts=0)

    # IMPORTANTE: Conectar buffers: salida Op_10 → entrada Op_70 (R1)
    entrada_op70_r1 = salida_op10  # Op_10_output ES la entrada de Op_70 (R1)
    salida_op70_r1 = controller.add_part_buffer('Op_70 (R1)_output', initial_parts=0)

    entrada_op70_r2 = controller.add_part_buffer('Op_70 (R2)_input', initial_parts=0)
    salida_op70_r2 = controller.add_part_buffer('Op_70 (R2)_output', initial_parts=0)

    # Definir operaciones con tiempos de trabajo configurables
    op_10 = Operation(
        name='Op_10',
        robot='R1',
        frames={'frame': 'R1_Op_10', 'afuera': 'R1_Op_10_Pos_Afuera'},
        speeds={'linear_mm_s': 500, 'joint_deg_s': 350},
        work_time_s=2.0,  # 2 segundos de procesamiento
        priority=2,
        passes=2,  # Se ejecuta 2 veces en el ciclo
        input_parts_needed=1,
        output_parts_generated=1
    )

    op_20 = Operation(
        name='Op_20',
        robot='R1',
        frames={'frame': 'R1_Op_20', 'dentro': 'R1_Op_20_Pos_Dentro'},
        speeds={'linear_mm_s': 500, 'joint_deg_s': 350},
        work_time_s=3.0,  # 3 segundos
        priority=3,
        passes=1,
        input_parts_needed=1,
        output_parts_generated=1
    )

    op_70_r1 = Operation(
        name='Op_70 (R1)',
        robot='R1',
        frames={'frame': 'R1_Op_70'},
        speeds={'linear_mm_s': 500},
        work_time_s=1.5,  # 1.5 segundos
        priority=5,
        requires_r2_free=False,
        passes=1,
        input_parts_needed=1,
        output_parts_generated=2  # Genera 2 piezas por cada entrada
    )

    op_70_r2 = Operation(
        name='Op_70 (R2)',
        robot='R2',
        frames={'frame': 'R2_Op_70'},
        speeds={'linear_mm_s': 500},
        work_time_s=2.0,
        priority=5,
        passes=1,
        input_parts_needed=1,
        output_parts_generated=1
    )

    op_80_r2 = Operation(
        name='Op_80 (R2)',
        robot='R2',
        frames={'frame': 'R2_Op_80'},
        speeds={'linear_mm_s': 500},
        work_time_s=1.0,
        priority=4,
        passes=1,
        input_parts_needed=1,
        output_parts_generated=1
    )

    # Añadir operaciones a la cola
    print("\n[INIT] Añadiendo operaciones a cola:")
    controller.add_operation_to_queue(op_10)
    controller.add_operation_to_queue(op_20)
    controller.add_operation_to_queue(op_70_r1)
    controller.add_operation_to_queue(op_70_r2)
    controller.add_operation_to_queue(op_80_r2)

    # Modificar tiempos de trabajo dinámicamente (ejemplo)
    print("\n[AJUSTES] Modificando tiempos de trabajo:")
    controller.set_operation_work_time('Op_10', work_time_s=1.5)  # Reducir Op_10 a 1.5s
    controller.set_operation_work_time('Op_20', work_time_s=2.5)  # Reducir Op_20 a 2.5s

    # Ejecutar ciclos (con callback dummy)
    def dummy_execute(op: Operation):
        """Callback de ejecución: simula movimiento."""
        print(f"    [ROBODK] Simulando movimiento: {op.frames}")

    print("\n[START] Iniciando ejecución de ciclos...")
    controller.run_all_cycles(callback_execute=dummy_execute)

    print("\n" + "="*60)
    print("FIN EJECUCIÓN")
    print("="*60)
