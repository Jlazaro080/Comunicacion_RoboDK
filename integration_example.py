"""
INTEGRATION GUIDE: Comunicacion_RoboDK + OperationScheduler
Ejemplo de cómo integrar el scheduler dinámico con el script de RoboDK
"""

import sys
import time
from robolink import *
from OperationScheduler import DynamicCycleController, Operation, OperationMetrics
from csv_loader import OperationConfigLoader
from operation_visualizer import GraphicalReport

# ==============================================================================
# PASO 1: Inicializar RoboDK y robots
# ==============================================================================

RDK = Robolink()
RDK.CloseStation()  # Cerrar sesión anterior
RDK.NewStation()    # Nueva sesión

print("="*80)
print("INTEGRACIÓN: RoboDK + Dynamic Operation Scheduler")
print("="*80)

# Cargar estación de trabajo
print("\n[PASO 1] Cargando estación RoboDK...")
try:
    # Intenta cargar una estación existente
    station = RDK.ItemUserPick("Selecciona archivo .stn de RoboDK")
    if not station.Valid():
        raise Exception("Estación no válida")
    print(f"  ✓ Estación cargada: {station.Name()}")
except Exception as e:
    print(f"  ⚠️  No se pudo cargar estación automáticamente: {e}")
    print("  Continuando con configuración manual...")

# Obtener robots
print("\n[PASO 2] Detectando robots...")
try:
    R1 = RDK.Item("R1", ITEM_TYPE_ROBOT)
    R2 = RDK.Item("R2", ITEM_TYPE_ROBOT)
    
    if R1.Valid():
        print(f"  ✓ R1 detectado: {R1.Name()}")
    if R2.Valid():
        print(f"  ✓ R2 detectado: {R2.Name()}")
except Exception as e:
    print(f"  ⚠️  Error detectando robots: {e}")

# ==============================================================================
# PASO 2: Crear scheduler y cargar operaciones desde CSV
# ==============================================================================

print("\n[PASO 3] Inicializando Dynamic Scheduler...")
controller = DynamicCycleController(num_r1=1, num_r2=1, total_cycles=2)

# Cargar configuraciones desde CSV
print("\n[PASO 3] Inicializando Dynamic Scheduler...")
controller = DynamicCycleController(max_cycles=2)

# Cargar configuraciones desde CSV
print("\n[PASO 4] Cargando operaciones desde CSV...")
loader = OperationConfigLoader()
csv_configs = loader.load_from_csv('operations_config.csv')

if csv_configs:
    for config_key in sorted(csv_configs.keys()):
        config = csv_configs[config_key]
        
        # Crear objeto Operation
        op = Operation(
            name=config.operation_name,
            robot=config.robot,
            frames={
                'primary': config.frames[0] if config.frames else 'frame',
                'targets': config.frames[1:] if len(config.frames) > 1 else []
            },
            speeds={
                'linear_mm_s': config.speeds_linear_mm_s,
                'joint_deg_s': config.speeds_joint_deg_s
            },
            work_time_s=config.work_time_s,
            priority=config.priority,
            passes=config.passes,
            input_parts_needed=config.input_parts,
            output_parts_generated=config.output_parts,
            requires_r2_free=config.requires_r2_free
        )
        
        controller.add_operation_to_queue(op)
        print(f"  ✓ {config.operation_name} ({config.robot}): " + 
              f"Prioridad {config.priority}, {config.work_time_s}s, "
              f"Entrada {config.input_parts}/Salida {config.output_parts}")
else:
    print("  ❌ No se pudieron cargar operaciones del CSV")
    sys.exit(1)

# ==============================================================================
# PASO 3: Definir callbacks para integración con RoboDK
# ==============================================================================

print("\n[PASO 5] Configurando callbacks de ejecución de RoboDK...")

# Esta sería la integración real con RoboDK
# (Adaptado del Comunicacion_RoboDk_V01.py)

def execute_operation_on_robot(operation: Operation):
    """
    Callback que ejecuta una operación en RoboDK
    
    Aquí iría la lógica real de:
    - Seleccionar el robot (R1/R2)
    - Cargar frames y targets
    - Ejecutar movimientos (MoveJ, MoveL)
    - Esperar completación (WaitMove)
    """
    
    print(f"\n  [RoboDK] Ejecutando {operation.name} en {operation.robot}")
    print(f"    - Frames: {operation.frames}")
    print(f"    - Velocidades: Lineal={operation.speeds.get('linear_mm_s', 'N/A')}mm/s, "
          f"Joint={operation.speeds.get('joint_deg_s', 'N/A')}°/s")
    print(f"    - Tiempo de procesamiento: {operation.work_time_s}s")
    
    # Seleccionar robot
    try:
        if operation.robot == 'R1':
            robot = RDK.Item("R1", ITEM_TYPE_ROBOT)
        elif operation.robot == 'R2':
            robot = RDK.Item("R2", ITEM_TYPE_ROBOT)
        else:
            print(f"    ⚠️  Robot desconocido: {operation.robot}")
            return
        
        if not robot.Valid():
            print(f"    ⚠️  Robot {operation.robot} no encontrado en RoboDK")
            return
        
        # AQUÍ iría la lógica real de RoboDK:
        # 1. Obtener frame: RDK.Item(operation.frames['primary'])
        # 2. Obtener targets: RDK.Item(target_name) para cada objetivo
        # 3. Ejecutar: robot.MoveJ(target), robot.MoveL(target), robot.WaitMove()
        # 4. Aplicar velocidades: robot.setSpeed(operation.speeds['linear_mm_s'])
        # 5. Esperar: time.sleep(operation.work_time_s) o robot.WaitMove()
        
        # Simulación del tiempo de procesamiento
        time.sleep(operation.work_time_s * 0.1)  # Escala 10x para demo rápida
        
        print(f"    ✓ Completada exitosamente")
        
    except Exception as e:
        print(f"    ❌ Error ejecutando operación: {e}")

# ==============================================================================
# PASO 4: Setup de piezas y ejecución
# ==============================================================================

print("\n[PASO 6] Configurando piezas iniciales...")

# Simular entrada de piezas
for op_name in ['Op_10']:
    controller.set_operation_work_time(op_name, 1.5)

print(f"  ✓ Piezas de entrada configuradas")

# ==============================================================================
# PASO 5: Ejecución y monitoreo
# ==============================================================================

print("\n[PASO 7] Iniciando ciclos de operación...")
print("="*80 + "\n")

# Inicializar métricas
metrics = OperationMetrics()
metrics.start_cycle()

cycle_count = 0
try:
    # Ejecutar ciclos dinámicamente
    cycle_count = controller.run_all_cycles(callback_execute=execute_operation_on_robot)
    
except KeyboardInterrupt:
    print("\n\n⚠️  Programa interrumpido por usuario")
except Exception as e:
    print(f"\n\n❌ Error durante ejecución: {e}")
    import traceback
    traceback.print_exc()

# ==============================================================================
# PASO 6: Reportes finales
# ==============================================================================

print("\n" + "="*80)
print("RESULTADO FINAL")
print("="*80)

controller.queue.print_summary()

print(f"\n📊 Resumen de ejecución:")
print(f"  ├─ Ciclos completados: {cycle_count}")
print(f"  ├─ Operaciones en cola: {len(controller.queue.operations)}")
print(f"  └─ Tiempo total: {metrics.total_time_s if hasattr(metrics, 'total_time_s') else 'N/A'}")

print("\n" + "="*80)
print("✅ INTEGRACIÓN COMPLETADA")
print("="*80)

print("\n📝 PRÓXIMOS PASOS:")
print("""
  1. Reemplazar execute_operation_on_robot() con la lógica real de RoboDK
  2. Integrar en el main loop de Comunicacion_RoboDk_V01.py
  3. Conectar buffers de piezas entre operaciones
  4. Añadir manejo de errores y recuperación
  5. Configurar dashboard de monitoreo (Tkinter)
""")
