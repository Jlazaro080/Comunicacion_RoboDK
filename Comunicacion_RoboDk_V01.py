import time
import sys
import difflib
import csv
import os
import threading
from datetime import datetime
from robodk import robolink


EXECUTION_MODE = 'HOME_PLUS_OPS'  # Opciones: 'HOME_ONLY', 'HOME_PLUS_OPS'
STRICT_OP_00_REQUIRED = False   # Solo aplica en HOME_PLUS_OPS
RUN_OP_10_SEQUENCE = True
STRICT_OP_10_REQUIRED = False
RUN_OP_20_SEQUENCE = True
STRICT_OP_20_REQUIRED = False
RUN_OP_30_SEQUENCE = True
STRICT_OP_30_REQUIRED = False
RUN_OP_50_SEQUENCE = True
STRICT_OP_50_REQUIRED = False
RUN_OP_60_SEQUENCE = True
STRICT_OP_60_REQUIRED = False
RUN_OP_70_SEQUENCE = True
STRICT_OP_70_REQUIRED = False
RUN_NOK_SEQUENCE = False
STRICT_NOK_REQUIRED = False
RUN_R2_SEQUENCE_FROM_OP70 = True
STRICT_R2_SEQUENCE_FROM_OP70_REQUIRED = False
RUN_R2_NOK_SEQUENCE = False
SEQUENCE_VERIFICATION_MODE = True
VERIFICATION_LINEAR_SPEED_MM_S = 5000
VERIFICATION_JOINT_SPEED_DEG_S = 2000
VERIFICATION_DWELL_S = 0.0
RUN_R2_IN_BACKGROUND = False
OP70_HANDSHAKE_TIMEOUT_S = 120.0
OP70_HANDSHAKE_POLL_S = 0.1
R1_SEQUENCE_CYCLES = 1  # 0 = infinito (R1 vuelve a Op_00 tras terminar Op_70)
OP_30_OPERATION_OPTION = os.getenv('OP30_OPTION', 'B').strip().upper()  # Opciones: 'A', 'B'
MONITOR_ONLY_ACTIVE_OP30_FRAME = True
FORCE_VISIBLE_TEST_MOVE = False
R1_OP_00_LINEAR_SPEED_MM_S = 500
R1_OP_00_JOINT_SPEED_DEG_S = 350
R1_OP_00_X_LINEAR_SPEED_MM_S = 120
R1_OP_00_X_JOINT_SPEED_DEG_S = 220
R1_OP_00_X_DWELL_S = 0.4
R1_OP_10_LINEAR_SPEED_MM_S = 500
R1_OP_10_JOINT_SPEED_DEG_S = 350
R1_OP_10_X_LINEAR_SPEED_MM_S = 120
R1_OP_10_X_JOINT_SPEED_DEG_S = 220
R1_OP_10_X_DWELL_S = 0.4
R1_OP_20_LINEAR_SPEED_MM_S = 500
R1_OP_20_JOINT_SPEED_DEG_S = 350
R1_OP_20_X_LINEAR_SPEED_MM_S = 120
R1_OP_20_X_JOINT_SPEED_DEG_S = 220
R1_OP_20_X_DWELL_S = 0.4
R1_OP_30_LINEAR_SPEED_MM_S = 500
R1_OP_30_JOINT_SPEED_DEG_S = 350
R1_OP_30_X_LINEAR_SPEED_MM_S = 120
R1_OP_30_X_JOINT_SPEED_DEG_S = 220
R1_OP_30_X_DWELL_S = 0.4
R1_OP_50_LINEAR_SPEED_MM_S = 500
R1_OP_50_JOINT_SPEED_DEG_S = 350
R1_OP_50_X_LINEAR_SPEED_MM_S = 120
R1_OP_50_X_JOINT_SPEED_DEG_S = 220
R1_OP_50_X_DWELL_S = 0.4
R1_OP_60_LINEAR_SPEED_MM_S = 500
R1_OP_60_JOINT_SPEED_DEG_S = 350
R1_OP_60_X_LINEAR_SPEED_MM_S = 120
R1_OP_60_X_JOINT_SPEED_DEG_S = 220
R1_OP_60_X_DWELL_S = 0.4
R1_OP_70_LINEAR_SPEED_MM_S = 500
R1_OP_70_JOINT_SPEED_DEG_S = 350
R1_OP_70_X_LINEAR_SPEED_MM_S = 120
R1_OP_70_X_JOINT_SPEED_DEG_S = 220
R1_OP_70_X_DWELL_S = 0.4
R2_OP_70_LINEAR_SPEED_MM_S = 500
R2_OP_70_JOINT_SPEED_DEG_S = 350
R2_OP_70_X_LINEAR_SPEED_MM_S = 120
R2_OP_70_X_JOINT_SPEED_DEG_S = 220
R2_OP_70_X_DWELL_S = 0.4
R2_OP_80_LINEAR_SPEED_MM_S = 500
R2_OP_80_JOINT_SPEED_DEG_S = 350
R2_OP_80_X_LINEAR_SPEED_MM_S = 120
R2_OP_80_X_JOINT_SPEED_DEG_S = 220
R2_OP_80_X_DWELL_S = 0.4
R2_OP_90_LINEAR_SPEED_MM_S = 500
R2_OP_90_JOINT_SPEED_DEG_S = 350
R2_OP_90_X_LINEAR_SPEED_MM_S = 120
R2_OP_90_X_JOINT_SPEED_DEG_S = 220
R2_OP_90_X_DWELL_S = 0.4
R2_OP_100_LINEAR_SPEED_MM_S = 500
R2_OP_100_JOINT_SPEED_DEG_S = 350
R2_OP_100_X_LINEAR_SPEED_MM_S = 120
R2_OP_100_X_JOINT_SPEED_DEG_S = 220
R2_OP_100_X_DWELL_S = 0.4
R2_OP_110_LINEAR_SPEED_MM_S = 500
R2_OP_110_JOINT_SPEED_DEG_S = 350
R2_OP_110_X_LINEAR_SPEED_MM_S = 120
R2_OP_110_X_JOINT_SPEED_DEG_S = 220
R2_OP_110_X_DWELL_S = 0.4
R2_OP_120_LINEAR_SPEED_MM_S = 500
R2_OP_120_JOINT_SPEED_DEG_S = 350
R2_OP_120_X_LINEAR_SPEED_MM_S = 120
R2_OP_120_X_JOINT_SPEED_DEG_S = 220
R2_OP_120_X_DWELL_S = 0.4
R2_OP_130_LINEAR_SPEED_MM_S = 500
R2_OP_130_JOINT_SPEED_DEG_S = 350
R2_OP_130_X_LINEAR_SPEED_MM_S = 120
R2_OP_130_X_JOINT_SPEED_DEG_S = 220
R2_OP_130_X_DWELL_S = 0.4
R2_OP_140_LINEAR_SPEED_MM_S = 500
R2_OP_140_JOINT_SPEED_DEG_S = 350
R2_OP_140_X_LINEAR_SPEED_MM_S = 120
R2_OP_140_X_JOINT_SPEED_DEG_S = 220
R2_OP_140_X_DWELL_S = 0.4
R2_NOK_LINEAR_SPEED_MM_S = 500
R2_NOK_JOINT_SPEED_DEG_S = 350
R2_NOK_X_LINEAR_SPEED_MM_S = 120
R2_NOK_X_JOINT_SPEED_DEG_S = 220
R2_NOK_X_DWELL_S = 0.4
R1_NOK_LINEAR_SPEED_MM_S = 500
R1_NOK_JOINT_SPEED_DEG_S = 350
R1_NOK_X_LINEAR_SPEED_MM_S = 120
R1_NOK_X_JOINT_SPEED_DEG_S = 220
R1_NOK_X_DWELL_S = 0.4
EXPORT_TIMES_CSV = True
TIMES_CSV_FILE = 'tiempos_robodk.csv'


def list_operation_item_names(rdk):
  names = []

  try:
    names = rdk.ItemList(list_names=True)
  except TypeError:
    names = []
  except Exception:
    names = []

  if not names:
    try:
      items = rdk.ItemList()
      names = [item.Name() for item in items if item.Valid()]
    except Exception:
      names = []

  return sorted(set([name for name in names if name]))


def print_missing_item_diagnostic(rdk, missing_name):
  print("=== Diagnóstico RoboDK ===")
  print(f"Item faltante: '{missing_name}'")

  item_names = list_operation_item_names(rdk)
  if not item_names:
    print("No se pudo recuperar el listado de items de la operación.")
    return

  suggestions = difflib.get_close_matches(missing_name, item_names, n=8, cutoff=0.5)
  if suggestions:
    print("Sugerencias de nombres parecidos:")
    for suggestion in suggestions:
      print(f"  - {suggestion}")
  else:
    print("No encontré coincidencias cercanas para ese nombre.")

  max_items_to_print = 80
  print(f"Items disponibles en la operación (mostrando hasta {max_items_to_print}):")
  for item_name in item_names[:max_items_to_print]:
    print(f"  - {item_name}")

  hidden_items = len(item_names) - max_items_to_print
  if hidden_items > 0:
    print(f"  ... y {hidden_items} item(s) más.")


def print_item_parent_chain(label, item, max_depth=8):
  if item is None:
    print(f"{label}: N/D")
    return

  try:
    if not item.Valid():
      print(f"{label}: inválido")
      return
  except Exception:
    print(f"{label}: inválido")
    return

  chain = []
  current = item
  for _ in range(max_depth):
    try:
      chain.append(current.Name())
    except Exception:
      break

    try:
      parent = current.Parent()
    except Exception:
      break

    if not parent or not parent.Valid():
      break
    current = parent

  print(f"{label}: {' <- '.join(chain)}")


def print_operations_hierarchy_diagnostic(frame_op20, frame_op30, op30_targets):
  print("\n=== Diagnóstico jerarquía de operaciones ===")
  print_item_parent_chain("Frame Op_20", frame_op20)
  print_item_parent_chain("Frame Op_30 activo", frame_op30)
  for target_label, target_item in op30_targets.items():
    print_item_parent_chain(target_label, target_item)


def item_is_descendant_of(item, expected_ancestor, max_depth=10):
  if item is None or expected_ancestor is None:
    return False
  try:
    if not item.Valid() or not expected_ancestor.Valid():
      return False
  except Exception:
    return False

  current = item
  for _ in range(max_depth):
    try:
      if current.Name() == expected_ancestor.Name():
        return True
      parent = current.Parent()
    except Exception:
      return False

    if not parent or not parent.Valid():
      return False
    current = parent

  return False


def assert_op30_targets_belong_to_selected_frame(selected_op30_frame, target_map):
  invalid_targets = []
  for target_name, target_item in target_map.items():
    if not item_is_descendant_of(target_item, selected_op30_frame):
      invalid_targets.append(target_name)

  if invalid_targets:
    raise Exception(
      f"Targets Op_30 no pertenecen al frame Op_30 seleccionado: {invalid_targets}. "
      "Verifica parentado en RoboDK."
    )


def get_item_or_raise(rdk, name):
  item = rdk.Item(name)
  if not item.Valid():
    print_missing_item_diagnostic(rdk, name)
    raise Exception(f"No encontré el item '{name}'. Verifica el nombre en el árbol de RoboDK.")
  return item


def get_first_valid_or_raise(rdk, names):
  for name in names:
    item = rdk.Item(name)
    if item.Valid():
      if name != names[0]:
        print(f"Usando alias encontrado para '{names[0]}': '{name}'")
      return item

  print_missing_item_diagnostic(rdk, names[0])
  raise Exception(f"No encontré ninguno de estos nombres: {names}")


def get_first_valid_optional(rdk, names):
  for name in names:
    item = rdk.Item(name)
    if item.Valid():
      if name != names[0]:
        print(f"Usando alias encontrado para '{names[0]}': '{name}'")
      return item
  return None


def do_visible_test_move(robot, robot_name, joint_index=0, delta_deg=15.0):
  joints_now = robot.Joints().list()
  if not joints_now or joint_index >= len(joints_now):
    print(f"No se pudo generar movimiento de prueba para {robot_name}.")
    return

  joints_test = joints_now.copy()
  joints_test[joint_index] = joints_test[joint_index] + delta_deg

  print(f"Movimiento de prueba visible para {robot_name} (J{joint_index + 1} +{delta_deg}°)")
  robot.MoveJ(joints_test)
  robot.MoveJ(joints_now)


def get_home_joints(robot, target_item):
  try:
    joints_from_target = target_item.Joints().list()
    joints_robot = robot.Joints().list()
    if joints_from_target and len(joints_from_target) == len(joints_robot):
      return joints_from_target
  except Exception:
    pass

  try:
    ik_result = robot.SolveIK(target_item.Pose())
    ik_joints = ik_result.list()
    joints_robot = robot.Joints().list()
    if ik_joints and len(ik_joints) == len(joints_robot):
      return ik_joints
  except Exception:
    pass

  return None


def move_robot_to_home(robot, robot_name, home_target):
  home_joints = get_home_joints(robot, home_target)
  if home_joints is not None:
    print(f"Inicio Home {robot_name} por juntas objetivo")
    robot.MoveJ(home_joints)
  else:
    print(f"Inicio Home {robot_name} por target directo")
    robot.MoveJ(home_target)

  robot.WaitMove()

  if home_joints is not None:
    final_joints = robot.Joints().list()
    max_joint_error = max(abs(final_joints[i] - home_joints[i]) for i in range(len(home_joints)))
    print(f"Error máximo de junta en Home {robot_name}: {max_joint_error:.4f}°")
  print(f"Fin de Home {robot_name}")


def execute_robot_step(robot, step_name, move_type, target):
  print(f"Inicio paso: {step_name}")

  if move_type == 'J':
    robot.MoveJ(target)
  elif move_type == 'L':
    robot.MoveL(target)
  else:
    raise Exception(f"Tipo de movimiento no soportado: {move_type}")

  robot.WaitMove()
  print(f"Fin paso: {step_name}")


def execute_robot_step_with_speed(robot, step_name, move_type, target, linear_speed_mm_s, joint_speed_deg_s):
  if SEQUENCE_VERIFICATION_MODE:
    linear_speed_mm_s = VERIFICATION_LINEAR_SPEED_MM_S
    joint_speed_deg_s = VERIFICATION_JOINT_SPEED_DEG_S
  robot.setSpeed(linear_speed_mm_s, joint_speed_deg_s)
  execute_robot_step(robot, step_name, move_type, target)


def execute_parallel_robot_step_with_speed(
  robot1,
  robot1_step_name,
  robot1_target,
  robot1_linear_speed_mm_s,
  robot1_joint_speed_deg_s,
  robot2,
  robot2_step_name,
  robot2_target,
  robot2_linear_speed_mm_s,
  robot2_joint_speed_deg_s,
  move_type,
):
  print(f"Inicio paso paralelo: {robot1_step_name} | {robot2_step_name}")

  robot1.setSpeed(robot1_linear_speed_mm_s, robot1_joint_speed_deg_s)
  robot2.setSpeed(robot2_linear_speed_mm_s, robot2_joint_speed_deg_s)

  try:
    if move_type == 'J':
      robot1.MoveJ(robot1_target, False)
      robot2.MoveJ(robot2_target, False)
    elif move_type == 'L':
      robot1.MoveL(robot1_target, False)
      robot2.MoveL(robot2_target, False)
    else:
      raise Exception(f"Tipo de movimiento no soportado: {move_type}")

    robot1.WaitMove()
    robot2.WaitMove()
  except TypeError:
    if move_type == 'J':
      robot1.MoveJ(robot1_target)
      robot2.MoveJ(robot2_target)
    elif move_type == 'L':
      robot1.MoveL(robot1_target)
      robot2.MoveL(robot2_target)
    else:
      raise Exception(f"Tipo de movimiento no soportado: {move_type}")

    robot1.WaitMove()
    robot2.WaitMove()

  print(f"Fin paso paralelo: {robot1_step_name} | {robot2_step_name}")


def execute_dwell(label, dwell_seconds):
  if SEQUENCE_VERIFICATION_MODE:
    dwell_seconds = VERIFICATION_DWELL_S
  if dwell_seconds <= 0:
    return
  print(f"Pausa en {label}: {dwell_seconds:.2f}s")
  time.sleep(dwell_seconds)


def execute_r2_operations_sequence_worker(state, robot, operation_sequence):
  try:
    for operation in operation_sequence:
      op_name = operation['op_name']
      frame_item = operation['frame']
      target_afuera = operation['target_afuera']
      target_dentro = operation['target_dentro']
      target_x = operation['target_x']
      linear_speed_mm_s = operation['linear_speed_mm_s']
      joint_speed_deg_s = operation['joint_speed_deg_s']
      x_linear_speed_mm_s = operation['x_linear_speed_mm_s']
      x_joint_speed_deg_s = operation['x_joint_speed_deg_s']
      x_dwell_s = operation['x_dwell_s']

      robot.setPoseFrame(frame_item)
      robot.setSpeed(linear_speed_mm_s, joint_speed_deg_s)
      robot.setRounding(0)

      print(f"Movimientos Robot 2 - Operación {op_name} (después de R1)")
      execute_robot_step_with_speed(robot, f'R2 -> {op_name}_Pos_Afuera (MoveJ)', 'J', target_afuera, linear_speed_mm_s, joint_speed_deg_s)
      execute_robot_step_with_speed(robot, f'R2 -> {op_name}_Pos_Dentro (MoveL)', 'L', target_dentro, linear_speed_mm_s, joint_speed_deg_s)
      execute_robot_step_with_speed(robot, f'R2 -> {op_name}_Pos_X (MoveL)', 'L', target_x, x_linear_speed_mm_s, x_joint_speed_deg_s)
      execute_dwell(f'R2 {op_name} Pos_X', x_dwell_s)
      execute_robot_step_with_speed(robot, f'R2 -> {op_name}_Pos_Afuera (MoveL)', 'L', target_afuera, linear_speed_mm_s, joint_speed_deg_s)

    state['completed_cycles'] = state.get('completed_cycles', 0) + 1
  except Exception as error:
    state['error'] = error


def get_robodk_sim_time(rdk):
  try:
    return float(rdk.SimulationTime())
  except Exception:
    return None


def get_pose_snapshot(item):
  if item is None:
    return None
  try:
    return str(item.PoseAbs())
  except Exception:
    return None


def get_pose_abs(item):
  if item is None:
    return None
  try:
    return item.PoseAbs()
  except Exception:
    return None


def get_changed_frame_names(before_snapshots, after_snapshots):
  changed_frames = []
  for frame_name in sorted(set(list(before_snapshots.keys()) + list(after_snapshots.keys()))):
    before_pose = before_snapshots.get(frame_name)
    after_pose = after_snapshots.get(frame_name)
    if before_pose is None or after_pose is None:
      continue
    if before_pose != after_pose:
      changed_frames.append(frame_name)
  return changed_frames


def print_frame_stability_report(before_snapshots, after_snapshots):
  print("\n=== Verificación de estabilidad de frames ===")
  for frame_name in sorted(set(list(before_snapshots.keys()) + list(after_snapshots.keys()))):
    before_pose = before_snapshots.get(frame_name)
    after_pose = after_snapshots.get(frame_name)

    if before_pose is None and after_pose is None:
      print(f"{frame_name}: N/D")
      continue

    if before_pose == after_pose:
      print(f"{frame_name}: SIN CAMBIOS")
    else:
      print(f"{frame_name}: CAMBIÓ")


def run_timed_block(label, rdk, timer_func, metrics, block_function):
  python_start = timer_func()
  robodk_start = get_robodk_sim_time(rdk)

  block_function()

  python_end = timer_func()
  robodk_end = get_robodk_sim_time(rdk)

  python_seconds = python_end - python_start
  robodk_seconds = None
  if robodk_start is not None and robodk_end is not None:
    robodk_seconds = robodk_end - robodk_start

  metrics[label] = {
    'python_s': python_seconds,
    'robodk_s': robodk_seconds,
  }


def print_timing_summary(metrics, total_python_s, total_robodk_s):
  print("\n=== Resumen de tiempos ===")
  for label, data in metrics.items():
    python_s = data['python_s']
    robodk_s = data['robodk_s']
    if robodk_s is None:
      print(f"{label}: Python={python_s:.3f}s | RoboDK=N/D")
    else:
      delta_s = python_s - robodk_s
      print(f"{label}: Python={python_s:.3f}s | RoboDK={robodk_s:.3f}s | Delta={delta_s:.3f}s")

  if total_robodk_s is None:
    print(f"TOTAL: Python={total_python_s:.3f}s | RoboDK=N/D")
  else:
    delta_total_s = total_python_s - total_robodk_s
    print(f"TOTAL: Python={total_python_s:.3f}s | RoboDK={total_robodk_s:.3f}s | Delta={delta_total_s:.3f}s")


def export_timing_summary_csv(metrics, total_python_s, total_robodk_s, csv_file):
  timestamp = datetime.now().isoformat(timespec='seconds')
  rows = []

  for label, data in metrics.items():
    python_s = data['python_s']
    robodk_s = data['robodk_s']
    delta_s = None if robodk_s is None else python_s - robodk_s
    rows.append({
      'timestamp': timestamp,
      'section': label,
      'python_s': f"{python_s:.6f}",
      'robodk_s': '' if robodk_s is None else f"{robodk_s:.6f}",
      'delta_s': '' if delta_s is None else f"{delta_s:.6f}",
    })

  total_delta_s = None if total_robodk_s is None else total_python_s - total_robodk_s
  rows.append({
    'timestamp': timestamp,
    'section': 'TOTAL',
    'python_s': f"{total_python_s:.6f}",
    'robodk_s': '' if total_robodk_s is None else f"{total_robodk_s:.6f}",
    'delta_s': '' if total_delta_s is None else f"{total_delta_s:.6f}",
  })

  file_exists = False
  try:
    with open(csv_file, 'r', newline='', encoding='utf-8'):
      file_exists = True
  except FileNotFoundError:
    file_exists = False

  with open(csv_file, 'a', newline='', encoding='utf-8') as csv_handle:
    writer = csv.DictWriter(csv_handle, fieldnames=['timestamp', 'section', 'python_s', 'robodk_s', 'delta_s'])
    if not file_exists:
      writer.writeheader()
    writer.writerows(rows)

  print(f"Resumen de tiempos exportado a: {csv_file}")


if sys.gettrace() is None:
    timer = time.time
else:
    timer = time.perf_counter


start_time = timer()

# Link to RoboDK
RDK = robolink.Robolink()
RDK.setRunMode(robolink.RUNMODE_SIMULATE)
RDK.setSimulationSpeed(1.0)
RDK.Render(True)

try:
  connection_state, connection_msg = RDK.ConnectedState()
  print(f"Estado conexión RoboDK: {connection_state} - {connection_msg}")
except Exception:
  print("No se pudo consultar el estado de conexión de RoboDK.")

robotR1 = get_item_or_raise(RDK, 'R1')
robotR2 = get_item_or_raise(RDK, 'R2')

# Posicion HOME
RDK_R1_Home_General = get_first_valid_or_raise(RDK, ['R1_Home_Gral', 'R1_Home_gral'])
RDK_R2_Home_General = get_first_valid_or_raise(RDK, ['R2_Home_Gral', 'R2_Home_gral'])

# Posiciones opcionales de Robot 1 (según operación)
frameR1_OP_00 = get_first_valid_optional(RDK, ['R1_Op_00'])
frameBase = get_first_valid_optional(RDK, ['R1_Base'])
RDK_R1_OP_00_Pos_Dentro = get_first_valid_optional(RDK, ['R1_Op_00_Pos_Dentro'])
RDK_R1_OP_00_Pos_X = get_first_valid_optional(RDK, ['R1_Op_00_Pos_X'])
RDK_R1_OP_00_Pos_Afuera = get_first_valid_optional(RDK, ['R1_Op_00_Pos_Afuera'])

frameR1_OP_10 = get_first_valid_optional(RDK, ['R1_Op_10'])
RDK_R1_OP_10_Pos_Dentro = get_first_valid_optional(RDK, ['R1_Op_10_Pos_Dentro'])
RDK_R1_OP_10_Pos_X = get_first_valid_optional(RDK, ['R1_Op_10_Pos_X'])
RDK_R1_OP_10_Pos_Afuera = get_first_valid_optional(RDK, ['R1_Op_10_Pos_Afuera'])

frameR1_OP_20 = get_first_valid_optional(RDK, ['R1_Op_20'])
RDK_R1_OP_20_Pos_Dentro = get_first_valid_optional(RDK, ['R1_Op_20_Pos_Dentro'])
RDK_R1_OP_20_Pos_X = get_first_valid_optional(RDK, ['R1_Op_20_Pos_X'])
RDK_R1_OP_20_Pos_Afuera = get_first_valid_optional(RDK, ['R1_Op_20_Pos_Afuera'])

frameR1_OP_30_A = get_first_valid_optional(RDK, ['R1_Op_30_A'])
RDK_R1_OP_30_A_Pos_Dentro = get_first_valid_optional(RDK, ['R1_Op_30_A_Pos_Dentro'])
RDK_R1_OP_30_A_Pos_X = get_first_valid_optional(RDK, ['R1_Op_30_A_Pos_X'])
RDK_R1_OP_30_A_Pos_Afuera = get_first_valid_optional(RDK, ['R1_Op_30_A_Pos_Afuera'])

frameR1_OP_30_B = get_first_valid_optional(RDK, ['R1_Op_30_B'])
RDK_R1_OP_30_B_Pos_Dentro = get_first_valid_optional(RDK, ['R1_Op_30_B_Pos_Dentro'])
RDK_R1_OP_30_B_Pos_X = get_first_valid_optional(RDK, ['R1_Op_30_B_Pos_X'])
RDK_R1_OP_30_B_Pos_Afuera = get_first_valid_optional(RDK, ['R1_Op_30_B_Pos_Afuera'])

frameR1_OP_50 = get_first_valid_optional(RDK, ['R1_Op_50'])
RDK_R1_OP_50_Pos_Dentro = get_first_valid_optional(RDK, ['R1_Op_50_Pos_Dentro'])
RDK_R1_OP_50_Pos_X = get_first_valid_optional(RDK, ['R1_Op_50_Pos_X'])
RDK_R1_OP_50_Pos_Afuera = get_first_valid_optional(RDK, ['R1_Op_50_Pos_Afuera'])

frameR1_OP_60 = get_first_valid_optional(RDK, ['R1_Op_60'])
RDK_R1_OP_60_Pos_Dentro = get_first_valid_optional(RDK, ['R1_Op_60_Pos_Dentro'])
RDK_R1_OP_60_Pos_X = get_first_valid_optional(RDK, ['R1_Op_60_Pos_X'])
RDK_R1_OP_60_Pos_Afuera = get_first_valid_optional(RDK, ['R1_Op_60_Pos_Afuera'])

frameR1_OP_70 = get_first_valid_optional(RDK, ['R1_Op_70'])
RDK_R1_OP_70_Pos_Dentro = get_first_valid_optional(RDK, ['R1_Op_70_Pos_Dentro'])
RDK_R1_OP_70_Pos_X = get_first_valid_optional(RDK, ['R1_Op_70_Pos_X'])
RDK_R1_OP_70_Pos_Afuera = get_first_valid_optional(RDK, ['R1_Op_70_Pos_Afuera'])

frameR2_OP_70 = get_first_valid_optional(RDK, ['R2_Op_70'])
RDK_R2_OP_70_Pos_Dentro = get_first_valid_optional(RDK, ['R2_Op_70_Pos_Dentro'])
RDK_R2_OP_70_Pos_X = get_first_valid_optional(RDK, ['R2_Op_70_Pos_X'])
RDK_R2_OP_70_Pos_Afuera = get_first_valid_optional(RDK, ['R2_Op_70_Pos_Afuera'])

frameR2_OP_80 = get_first_valid_optional(RDK, ['R2_Op_80'])
RDK_R2_OP_80_Pos_Dentro = get_first_valid_optional(RDK, ['R2_Op_80_Pos_Dentro'])
RDK_R2_OP_80_Pos_X = get_first_valid_optional(RDK, ['R2_Op_80_Pos_X'])
RDK_R2_OP_80_Pos_Afuera = get_first_valid_optional(RDK, ['R2_Op_80_Pos_Afuera'])

frameR2_OP_90 = get_first_valid_optional(RDK, ['R2_Op_90'])
RDK_R2_OP_90_Pos_Dentro = get_first_valid_optional(RDK, ['R2_Op_90_Pos_Dentro'])
RDK_R2_OP_90_Pos_X = get_first_valid_optional(RDK, ['R2_Op_90_Pos_X'])
RDK_R2_OP_90_Pos_Afuera = get_first_valid_optional(RDK, ['R2_Op_90_Pos_Afuera'])

frameR2_OP_100 = get_first_valid_optional(RDK, ['R2_Op_100'])
RDK_R2_OP_100_Pos_Dentro = get_first_valid_optional(RDK, ['R2_Op_100_Pos_Dentro'])
RDK_R2_OP_100_Pos_X = get_first_valid_optional(RDK, ['R2_Op_100_Pos_X'])
RDK_R2_OP_100_Pos_Afuera = get_first_valid_optional(RDK, ['R2_Op_100_Pos_Afuera'])

frameR2_OP_110 = get_first_valid_optional(RDK, ['R2_Op_110'])
RDK_R2_OP_110_Pos_Dentro = get_first_valid_optional(RDK, ['R2_Op_110_Pos_Dentro'])
RDK_R2_OP_110_Pos_X = get_first_valid_optional(RDK, ['R2_Op_110_Pos_X'])
RDK_R2_OP_110_Pos_Afuera = get_first_valid_optional(RDK, ['R2_Op_110_Pos_Afuera'])

frameR2_OP_120 = get_first_valid_optional(RDK, ['R2_Op_120'])
RDK_R2_OP_120_Pos_Dentro = get_first_valid_optional(RDK, ['R2_Op_120_Pos_Dentro'])
RDK_R2_OP_120_Pos_X = get_first_valid_optional(RDK, ['R2_Op_120_Pos_X'])
RDK_R2_OP_120_Pos_Afuera = get_first_valid_optional(RDK, ['R2_Op_120_Pos_Afuera'])

frameR2_OP_130 = get_first_valid_optional(RDK, ['R2_Op_130'])
RDK_R2_OP_130_Pos_Dentro = get_first_valid_optional(RDK, ['R2_Op_130_Pos_Dentro'])
RDK_R2_OP_130_Pos_X = get_first_valid_optional(RDK, ['R2_Op_130_Pos_X'])
RDK_R2_OP_130_Pos_Afuera = get_first_valid_optional(RDK, ['R2_Op_130_Pos_Afuera'])

frameR2_OP_140 = get_first_valid_optional(RDK, ['R2_Op_140'])
RDK_R2_OP_140_Pos_Dentro = get_first_valid_optional(RDK, ['R2_Op_140_Pos_Dentro'])
RDK_R2_OP_140_Pos_X = get_first_valid_optional(RDK, ['R2_Op_140_Pos_X'])
RDK_R2_OP_140_Pos_Afuera = get_first_valid_optional(RDK, ['R2_Op_140_Pos_Afuera'])

frameR2_NOK = get_first_valid_optional(RDK, ['R2_Nok', 'R2_nok', 'R2_NOK'])
RDK_R2_NOK_Pos_Dentro = get_first_valid_optional(RDK, ['R2_Nok_Pos_Dentro', 'R2_nok_Pos_Dentro', 'R2_NOK_Pos_Dentro'])
RDK_R2_NOK_Pos_X = get_first_valid_optional(RDK, ['R2_Nok_Pos_X', 'R2_nok_Pos_X', 'R2_NOK_Pos_X'])
RDK_R2_NOK_Pos_Afuera = get_first_valid_optional(RDK, ['R2_Nok_Pos_Afuera', 'R2_nok_Pos_Afuera', 'R2_NOK_Pos_Afuera'])

frameR1_NOK = get_first_valid_optional(RDK, ['R1_nok', 'R1_NOK'])
RDK_R1_NOK_Pos_Dentro = get_first_valid_optional(RDK, ['R1_nok_Pos_Dentro', 'R1_NOK_Pos_Dentro'])
RDK_R1_NOK_Pos_X = get_first_valid_optional(RDK, ['R1_nok_Pos_X', 'R1_NOK_Pos_X'])
RDK_R1_NOK_Pos_Afuera = get_first_valid_optional(RDK, ['R1_nok_Pos_Afuera', 'R1_NOK_Pos_Afuera'])

if OP_30_OPERATION_OPTION not in ('A', 'B'):
  raise Exception("OP_30_OPERATION_OPTION inválido. Usa 'A' o 'B'.")

if OP_30_OPERATION_OPTION == 'A':
  frameR1_OP_30 = frameR1_OP_30_A
  RDK_R1_OP_30_Pos_Dentro = RDK_R1_OP_30_A_Pos_Dentro
  RDK_R1_OP_30_Pos_X = RDK_R1_OP_30_A_Pos_X
  RDK_R1_OP_30_Pos_Afuera = RDK_R1_OP_30_A_Pos_Afuera
else:
  frameR1_OP_30 = frameR1_OP_30_B
  RDK_R1_OP_30_Pos_Dentro = RDK_R1_OP_30_B_Pos_Dentro
  RDK_R1_OP_30_Pos_X = RDK_R1_OP_30_B_Pos_X
  RDK_R1_OP_30_Pos_Afuera = RDK_R1_OP_30_B_Pos_Afuera

op_00_required_items = {
  'R1_Op_00': frameR1_OP_00,
  'R1_Op_00_Pos_Dentro': RDK_R1_OP_00_Pos_Dentro,
  'R1_Op_00_Pos_X': RDK_R1_OP_00_Pos_X,
  'R1_Op_00_Pos_Afuera': RDK_R1_OP_00_Pos_Afuera,
}

missing_op_00_items = [name for name, value in op_00_required_items.items() if value is None]

sequence_op_00_items_found = all([
  frameR1_OP_00 is not None,
  RDK_R1_OP_00_Pos_Dentro is not None,
  RDK_R1_OP_00_Pos_X is not None,
  RDK_R1_OP_00_Pos_Afuera is not None
])

op_10_required_items = {
  'R1_Op_10': frameR1_OP_10,
  'R1_Op_10_Pos_Dentro': RDK_R1_OP_10_Pos_Dentro,
  'R1_Op_10_Pos_X': RDK_R1_OP_10_Pos_X,
  'R1_Op_10_Pos_Afuera': RDK_R1_OP_10_Pos_Afuera,
}

missing_op_10_items = [name for name, value in op_10_required_items.items() if value is None]

sequence_op_10_items_found = all([
  frameR1_OP_10 is not None,
  RDK_R1_OP_10_Pos_Dentro is not None,
  RDK_R1_OP_10_Pos_X is not None,
  RDK_R1_OP_10_Pos_Afuera is not None
])

op_20_required_items = {
  'R1_Op_20': frameR1_OP_20,
  'R1_Op_20_Pos_Dentro': RDK_R1_OP_20_Pos_Dentro,
  'R1_Op_20_Pos_X': RDK_R1_OP_20_Pos_X,
  'R1_Op_20_Pos_Afuera': RDK_R1_OP_20_Pos_Afuera,
}

missing_op_20_items = [name for name, value in op_20_required_items.items() if value is None]

sequence_op_20_items_found = all([
  frameR1_OP_20 is not None,
  RDK_R1_OP_20_Pos_Dentro is not None,
  RDK_R1_OP_20_Pos_X is not None,
  RDK_R1_OP_20_Pos_Afuera is not None
])

op_30_required_items = {
  f'R1_Op_30_{OP_30_OPERATION_OPTION}': frameR1_OP_30,
  f'R1_Op_30_{OP_30_OPERATION_OPTION}_Pos_Dentro': RDK_R1_OP_30_Pos_Dentro,
  f'R1_Op_30_{OP_30_OPERATION_OPTION}_Pos_X': RDK_R1_OP_30_Pos_X,
  f'R1_Op_30_{OP_30_OPERATION_OPTION}_Pos_Afuera': RDK_R1_OP_30_Pos_Afuera,
}

missing_op_30_items = [name for name, value in op_30_required_items.items() if value is None]

sequence_op_30_items_found = all([
  frameR1_OP_30 is not None,
  RDK_R1_OP_30_Pos_Dentro is not None,
  RDK_R1_OP_30_Pos_X is not None,
  RDK_R1_OP_30_Pos_Afuera is not None
])

op_50_required_items = {
  'R1_Op_50': frameR1_OP_50,
  'R1_Op_50_Pos_Dentro': RDK_R1_OP_50_Pos_Dentro,
  'R1_Op_50_Pos_X': RDK_R1_OP_50_Pos_X,
  'R1_Op_50_Pos_Afuera': RDK_R1_OP_50_Pos_Afuera,
}

missing_op_50_items = [name for name, value in op_50_required_items.items() if value is None]

sequence_op_50_items_found = all([
  frameR1_OP_50 is not None,
  RDK_R1_OP_50_Pos_Dentro is not None,
  RDK_R1_OP_50_Pos_X is not None,
  RDK_R1_OP_50_Pos_Afuera is not None
])

op_60_required_items = {
  'R1_Op_60': frameR1_OP_60,
  'R1_Op_60_Pos_Dentro': RDK_R1_OP_60_Pos_Dentro,
  'R1_Op_60_Pos_X': RDK_R1_OP_60_Pos_X,
  'R1_Op_60_Pos_Afuera': RDK_R1_OP_60_Pos_Afuera,
}

missing_op_60_items = [name for name, value in op_60_required_items.items() if value is None]

sequence_op_60_items_found = all([
  frameR1_OP_60 is not None,
  RDK_R1_OP_60_Pos_Dentro is not None,
  RDK_R1_OP_60_Pos_X is not None,
  RDK_R1_OP_60_Pos_Afuera is not None
])

op_70_required_items = {
  'R1_Op_70': frameR1_OP_70,
  'R1_Op_70_Pos_Dentro': RDK_R1_OP_70_Pos_Dentro,
  'R1_Op_70_Pos_X': RDK_R1_OP_70_Pos_X,
  'R1_Op_70_Pos_Afuera': RDK_R1_OP_70_Pos_Afuera,
}

missing_op_70_items = [name for name, value in op_70_required_items.items() if value is None]

sequence_op_70_items_found = all([
  frameR1_OP_70 is not None,
  RDK_R1_OP_70_Pos_Dentro is not None,
  RDK_R1_OP_70_Pos_X is not None,
  RDK_R1_OP_70_Pos_Afuera is not None
])

r2_sequence_required_items = {
  'Op_70': {
    'R2_Op_70': frameR2_OP_70,
    'R2_Op_70_Pos_Dentro': RDK_R2_OP_70_Pos_Dentro,
    'R2_Op_70_Pos_X': RDK_R2_OP_70_Pos_X,
    'R2_Op_70_Pos_Afuera': RDK_R2_OP_70_Pos_Afuera,
  },
  'Op_80': {
    'R2_Op_80': frameR2_OP_80,
    'R2_Op_80_Pos_Dentro': RDK_R2_OP_80_Pos_Dentro,
    'R2_Op_80_Pos_X': RDK_R2_OP_80_Pos_X,
    'R2_Op_80_Pos_Afuera': RDK_R2_OP_80_Pos_Afuera,
  },
  'Op_90': {
    'R2_Op_90': frameR2_OP_90,
    'R2_Op_90_Pos_Dentro': RDK_R2_OP_90_Pos_Dentro,
    'R2_Op_90_Pos_X': RDK_R2_OP_90_Pos_X,
    'R2_Op_90_Pos_Afuera': RDK_R2_OP_90_Pos_Afuera,
  },
  'Op_100': {
    'R2_Op_100': frameR2_OP_100,
    'R2_Op_100_Pos_Dentro': RDK_R2_OP_100_Pos_Dentro,
    'R2_Op_100_Pos_X': RDK_R2_OP_100_Pos_X,
    'R2_Op_100_Pos_Afuera': RDK_R2_OP_100_Pos_Afuera,
  },
  'Op_110': {
    'R2_Op_110': frameR2_OP_110,
    'R2_Op_110_Pos_Dentro': RDK_R2_OP_110_Pos_Dentro,
    'R2_Op_110_Pos_X': RDK_R2_OP_110_Pos_X,
    'R2_Op_110_Pos_Afuera': RDK_R2_OP_110_Pos_Afuera,
  },
  'Op_120': {
    'R2_Op_120': frameR2_OP_120,
    'R2_Op_120_Pos_Dentro': RDK_R2_OP_120_Pos_Dentro,
    'R2_Op_120_Pos_X': RDK_R2_OP_120_Pos_X,
    'R2_Op_120_Pos_Afuera': RDK_R2_OP_120_Pos_Afuera,
  },
  'Op_130': {
    'R2_Op_130': frameR2_OP_130,
    'R2_Op_130_Pos_Dentro': RDK_R2_OP_130_Pos_Dentro,
    'R2_Op_130_Pos_X': RDK_R2_OP_130_Pos_X,
    'R2_Op_130_Pos_Afuera': RDK_R2_OP_130_Pos_Afuera,
  },
  'Op_140': {
    'R2_Op_140': frameR2_OP_140,
    'R2_Op_140_Pos_Dentro': RDK_R2_OP_140_Pos_Dentro,
    'R2_Op_140_Pos_X': RDK_R2_OP_140_Pos_X,
    'R2_Op_140_Pos_Afuera': RDK_R2_OP_140_Pos_Afuera,
  },
}

missing_r2_sequence_items = {
  op_name: [name for name, value in op_required_items.items() if value is None]
  for op_name, op_required_items in r2_sequence_required_items.items()
}

sequence_r2_items_found = all([
  len(missing_items) == 0 for missing_items in missing_r2_sequence_items.values()
])

r2_nok_required_items = {
  'R2_Nok': frameR2_NOK,
  'R2_Nok_Pos_Dentro': RDK_R2_NOK_Pos_Dentro,
  'R2_Nok_Pos_X': RDK_R2_NOK_Pos_X,
  'R2_Nok_Pos_Afuera': RDK_R2_NOK_Pos_Afuera,
}

missing_r2_nok_items = [name for name, value in r2_nok_required_items.items() if value is None]

sequence_r2_nok_items_found = all([
  frameR2_NOK is not None,
  RDK_R2_NOK_Pos_Dentro is not None,
  RDK_R2_NOK_Pos_X is not None,
  RDK_R2_NOK_Pos_Afuera is not None,
])

nok_required_items = {
  'R1_nok': frameR1_NOK,
  'R1_nok_Pos_Dentro': RDK_R1_NOK_Pos_Dentro,
  'R1_nok_Pos_X': RDK_R1_NOK_Pos_X,
  'R1_nok_Pos_Afuera': RDK_R1_NOK_Pos_Afuera,
}

missing_nok_items = [name for name, value in nok_required_items.items() if value is None]

sequence_nok_items_found = all([
  frameR1_NOK is not None,
  RDK_R1_NOK_Pos_Dentro is not None,
  RDK_R1_NOK_Pos_X is not None,
  RDK_R1_NOK_Pos_Afuera is not None
])

if EXECUTION_MODE not in ('HOME_ONLY', 'HOME_PLUS_OPS'):
  raise Exception("EXECUTION_MODE inválido. Usa 'HOME_ONLY' o 'HOME_PLUS_OPS'.")

run_ops_sequences = EXECUTION_MODE == 'HOME_PLUS_OPS'

if run_ops_sequences:
  if missing_op_00_items:
    print("Elementos faltantes para secuencia Op_00:")
    for missing_item in missing_op_00_items:
      print(f"  - {missing_item}")
  else:
    print("Secuencia Op_00 lista: todos los elementos requeridos están disponibles.")

  if RUN_OP_10_SEQUENCE:
    if missing_op_10_items:
      print("Elementos faltantes para secuencia Op_10:")
      for missing_item in missing_op_10_items:
        print(f"  - {missing_item}")
    else:
      print("Secuencia Op_10 lista: todos los elementos requeridos están disponibles.")

  if RUN_OP_20_SEQUENCE:
    if missing_op_20_items:
      print("Elementos faltantes para secuencia Op_20:")
      for missing_item in missing_op_20_items:
        print(f"  - {missing_item}")
    else:
      print("Secuencia Op_20 lista: todos los elementos requeridos están disponibles.")

  if RUN_OP_30_SEQUENCE:
    if missing_op_30_items:
      print(f"Elementos faltantes para secuencia Op_30_{OP_30_OPERATION_OPTION}:")
      for missing_item in missing_op_30_items:
        print(f"  - {missing_item}")
    else:
      print(f"Secuencia Op_30_{OP_30_OPERATION_OPTION} lista: todos los elementos requeridos están disponibles.")

  if RUN_OP_50_SEQUENCE:
    if missing_op_50_items:
      print("Elementos faltantes para secuencia Op_50:")
      for missing_item in missing_op_50_items:
        print(f"  - {missing_item}")
    else:
      print("Secuencia Op_50 lista: todos los elementos requeridos están disponibles.")

  if RUN_OP_60_SEQUENCE:
    if missing_op_60_items:
      print("Elementos faltantes para secuencia Op_60:")
      for missing_item in missing_op_60_items:
        print(f"  - {missing_item}")
    else:
      print("Secuencia Op_60 lista: todos los elementos requeridos están disponibles.")

  if RUN_OP_70_SEQUENCE:
    if missing_op_70_items:
      print("Elementos faltantes para secuencia Op_70:")
      for missing_item in missing_op_70_items:
        print(f"  - {missing_item}")
    else:
      print("Secuencia Op_70 lista: todos los elementos requeridos están disponibles.")

  if RUN_OP_70_SEQUENCE and RUN_R2_SEQUENCE_FROM_OP70:
    for op_name, missing_items in missing_r2_sequence_items.items():
      if missing_items:
        print(f"Elementos faltantes para secuencia R2_{op_name}:")
        for missing_item in missing_items:
          print(f"  - {missing_item}")
      else:
        print(f"Secuencia R2_{op_name} lista: todos los elementos requeridos están disponibles.")

  if RUN_OP_70_SEQUENCE and RUN_R2_SEQUENCE_FROM_OP70 and RUN_R2_NOK_SEQUENCE:
    if missing_r2_nok_items:
      print("Elementos faltantes para secuencia opcional R2_Nok:")
      for missing_item in missing_r2_nok_items:
        print(f"  - {missing_item}")
    else:
      print("Secuencia opcional R2_Nok lista: todos los elementos requeridos están disponibles.")

  if RUN_NOK_SEQUENCE:
    if missing_nok_items:
      print("Elementos faltantes para secuencia NOK:")
      for missing_item in missing_nok_items:
        print(f"  - {missing_item}")
    else:
      print("Secuencia NOK lista: todos los elementos requeridos están disponibles.")

if run_ops_sequences and STRICT_OP_00_REQUIRED and not sequence_op_00_items_found:
  raise Exception(f"Modo HOME_PLUS_OPS estricto: faltan elementos Op_00: {missing_op_00_items}")

if run_ops_sequences and RUN_OP_10_SEQUENCE and STRICT_OP_10_REQUIRED and not sequence_op_10_items_found:
  raise Exception(f"Secuencia Op_10 estricta: faltan elementos Op_10: {missing_op_10_items}")

if run_ops_sequences and RUN_OP_20_SEQUENCE and STRICT_OP_20_REQUIRED and not sequence_op_20_items_found:
  raise Exception(f"Secuencia Op_20 estricta: faltan elementos Op_20: {missing_op_20_items}")

if run_ops_sequences and RUN_OP_30_SEQUENCE and STRICT_OP_30_REQUIRED and not sequence_op_30_items_found:
  raise Exception(f"Secuencia Op_30 estricta: faltan elementos Op_30: {missing_op_30_items}")

if run_ops_sequences and RUN_OP_50_SEQUENCE and STRICT_OP_50_REQUIRED and not sequence_op_50_items_found:
  raise Exception(f"Secuencia Op_50 estricta: faltan elementos Op_50: {missing_op_50_items}")

if run_ops_sequences and RUN_OP_60_SEQUENCE and STRICT_OP_60_REQUIRED and not sequence_op_60_items_found:
  raise Exception(f"Secuencia Op_60 estricta: faltan elementos Op_60: {missing_op_60_items}")

if run_ops_sequences and RUN_OP_70_SEQUENCE and STRICT_OP_70_REQUIRED and not sequence_op_70_items_found:
  raise Exception(f"Secuencia Op_70 estricta: faltan elementos Op_70: {missing_op_70_items}")

if run_ops_sequences and RUN_OP_70_SEQUENCE and RUN_R2_SEQUENCE_FROM_OP70 and STRICT_R2_SEQUENCE_FROM_OP70_REQUIRED and not sequence_r2_items_found:
  raise Exception(f"Secuencia R2 desde Op_70 estricta: faltan elementos por operación: {missing_r2_sequence_items}")

if run_ops_sequences and RUN_OP_70_SEQUENCE and RUN_R2_SEQUENCE_FROM_OP70 and RUN_R2_NOK_SEQUENCE and STRICT_R2_SEQUENCE_FROM_OP70_REQUIRED and not sequence_r2_nok_items_found:
  raise Exception(f"Secuencia opcional R2_Nok estricta: faltan elementos R2_Nok: {missing_r2_nok_items}")

if run_ops_sequences and RUN_NOK_SEQUENCE and STRICT_NOK_REQUIRED and not sequence_nok_items_found:
  raise Exception(f"Secuencia NOK estricta: faltan elementos NOK: {missing_nok_items}")

try:
  section_times = {}
  r2_sequence_state = {
    'thread': None,
    'error': None,
    'dispatched_cycles': 0,
    'completed_cycles': 0,
  }
  total_robodk_start = get_robodk_sim_time(RDK)
  if MONITOR_ONLY_ACTIVE_OP30_FRAME:
    monitored_frames = {
      f'R1_Op_30_{OP_30_OPERATION_OPTION}': frameR1_OP_30,
    }
  else:
    monitored_frames = {
      'R1_Op_00': frameR1_OP_00,
      'R1_Op_10': frameR1_OP_10,
      'R1_Op_20': frameR1_OP_20,
      f'R1_Op_30_{OP_30_OPERATION_OPTION}': frameR1_OP_30,
      'R1_Op_50': frameR1_OP_50,
      'R1_Op_60': frameR1_OP_60,
      'R1_Op_70': frameR1_OP_70,
      'R2_Op_70': frameR2_OP_70,
      'R2_Op_80': frameR2_OP_80,
      'R2_Op_90': frameR2_OP_90,
      'R2_Op_100': frameR2_OP_100,
      'R2_Op_110': frameR2_OP_110,
      'R2_Op_120': frameR2_OP_120,
      'R2_Op_130': frameR2_OP_130,
      'R2_Op_140': frameR2_OP_140,
      'R2_Nok': frameR2_NOK,
      'R1_nok': frameR1_NOK,
    }

  frame_snapshots_before = {
    frame_name: get_pose_snapshot(frame_item)
    for frame_name, frame_item in monitored_frames.items()
  }

  print_operations_hierarchy_diagnostic(
    frameR1_OP_20,
    frameR1_OP_30,
    {
      'Op_30 Pos_Afuera': RDK_R1_OP_30_Pos_Afuera,
      'Op_30 Pos_Dentro': RDK_R1_OP_30_Pos_Dentro,
      'Op_30 Pos_X': RDK_R1_OP_30_Pos_X,
    },
  )

  if frameBase is not None:
    robotR1.setPoseFrame(frameBase)

  print(f"Modo de ejecución RoboDK: {RDK.RunMode()} (esperado: {robolink.RUNMODE_SIMULATE})")
  print(f"Juntas iniciales R1: {robotR1.Joints().list()}")
  print(f"Juntas iniciales R2: {robotR2.Joints().list()}")

  robotR1.setSpeed(80, 150)
  run_timed_block(
    'Home R1',
    RDK,
    timer,
    section_times,
    lambda: move_robot_to_home(robotR1, 'R1', RDK_R1_Home_General),
  )

  robotR2.setSpeed(80, 150)
  run_timed_block(
    'Home R2',
    RDK,
    timer,
    section_times,
    lambda: move_robot_to_home(robotR2, 'R2', RDK_R2_Home_General),
  )

  if run_ops_sequences and sequence_op_00_items_found:
    cycle_number = 0
    while True:
      cycle_number = cycle_number + 1
      print(f"\n=== Ciclo R1 #{cycle_number} ===")

      #############################Movimientos Robot 1
      robotR1.setPoseFrame(frameR1_OP_00)
      robotR1.setSpeed(R1_OP_00_LINEAR_SPEED_MM_S, R1_OP_00_JOINT_SPEED_DEG_S)
      robotR1.setRounding(0)

      print("Movimientos Robot 1")
      run_timed_block(
        'Operación Op_00',
        RDK,
        timer,
        section_times,
        lambda: (
          execute_robot_step_with_speed(robotR1, 'R1 -> Op_00_Pos_Afuera (MoveJ)', 'J', RDK_R1_OP_00_Pos_Afuera, R1_OP_00_LINEAR_SPEED_MM_S, R1_OP_00_JOINT_SPEED_DEG_S),
          execute_robot_step_with_speed(robotR1, 'R1 -> Op_00_Pos_Dentro (MoveL)', 'L', RDK_R1_OP_00_Pos_Dentro, R1_OP_00_LINEAR_SPEED_MM_S, R1_OP_00_JOINT_SPEED_DEG_S),
          execute_robot_step_with_speed(robotR1, 'R1 -> Op_00_Pos_X (MoveL)', 'L', RDK_R1_OP_00_Pos_X, R1_OP_00_X_LINEAR_SPEED_MM_S, R1_OP_00_X_JOINT_SPEED_DEG_S),
          execute_dwell('Op_00 Pos_X', R1_OP_00_X_DWELL_S),
          execute_robot_step_with_speed(robotR1, 'R1 -> Op_00_Pos_Afuera (MoveL)', 'L', RDK_R1_OP_00_Pos_Afuera, R1_OP_00_LINEAR_SPEED_MM_S, R1_OP_00_JOINT_SPEED_DEG_S),
        ),
      )

      if RUN_OP_10_SEQUENCE and sequence_op_10_items_found:
        robotR1.setPoseFrame(frameR1_OP_10)
        robotR1.setSpeed(R1_OP_10_LINEAR_SPEED_MM_S, R1_OP_10_JOINT_SPEED_DEG_S)
        robotR1.setRounding(0)

        print("Movimientos Robot 1 - Operación Op_10")
        run_timed_block(
          'Operación Op_10',
          RDK,
          timer,
          section_times,
          lambda: (
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_10_Pos_Afuera (MoveJ)', 'J', RDK_R1_OP_10_Pos_Afuera, R1_OP_10_LINEAR_SPEED_MM_S, R1_OP_10_JOINT_SPEED_DEG_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_10_Pos_Dentro (MoveL)', 'L', RDK_R1_OP_10_Pos_Dentro, R1_OP_10_LINEAR_SPEED_MM_S, R1_OP_10_JOINT_SPEED_DEG_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_10_Pos_X (MoveL)', 'L', RDK_R1_OP_10_Pos_X, R1_OP_10_X_LINEAR_SPEED_MM_S, R1_OP_10_X_JOINT_SPEED_DEG_S),
            execute_dwell('Op_10 Pos_X', R1_OP_10_X_DWELL_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_10_Pos_Afuera (MoveL)', 'L', RDK_R1_OP_10_Pos_Afuera, R1_OP_10_LINEAR_SPEED_MM_S, R1_OP_10_JOINT_SPEED_DEG_S),
          ),
        )
      elif RUN_OP_10_SEQUENCE:
        print("Secuencia Op_10 omitida: faltan frame/targets en esta operación.")

      if RUN_OP_20_SEQUENCE and sequence_op_20_items_found:
        robotR1.setPoseFrame(frameR1_OP_20)
        robotR1.setSpeed(R1_OP_20_LINEAR_SPEED_MM_S, R1_OP_20_JOINT_SPEED_DEG_S)
        robotR1.setRounding(0)

        print("Movimientos Robot 1 - Operación Op_20")
        run_timed_block(
          'Operación Op_20',
          RDK,
          timer,
          section_times,
          lambda: (
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_20_Pos_Afuera (MoveJ)', 'J', RDK_R1_OP_20_Pos_Afuera, R1_OP_20_LINEAR_SPEED_MM_S, R1_OP_20_JOINT_SPEED_DEG_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_20_Pos_Dentro (MoveL)', 'L', RDK_R1_OP_20_Pos_Dentro, R1_OP_20_LINEAR_SPEED_MM_S, R1_OP_20_JOINT_SPEED_DEG_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_20_Pos_X (MoveL)', 'L', RDK_R1_OP_20_Pos_X, R1_OP_20_X_LINEAR_SPEED_MM_S, R1_OP_20_X_JOINT_SPEED_DEG_S),
            execute_dwell('Op_20 Pos_X', R1_OP_20_X_DWELL_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_20_Pos_Afuera (MoveL)', 'L', RDK_R1_OP_20_Pos_Afuera, R1_OP_20_LINEAR_SPEED_MM_S, R1_OP_20_JOINT_SPEED_DEG_S),
          ),
        )
      elif RUN_OP_20_SEQUENCE:
        print("Secuencia Op_20 omitida: faltan frame/targets en esta operación.")

      if RUN_OP_30_SEQUENCE and sequence_op_30_items_found:
        if OP_30_OPERATION_OPTION == 'A':
          frameR1_OP_30_runtime = get_first_valid_or_raise(RDK, ['R1_Op_30_A'])
        else:
          frameR1_OP_30_runtime = get_first_valid_or_raise(RDK, ['R1_Op_30_B'])

        assert_op30_targets_belong_to_selected_frame(
          frameR1_OP_30_runtime,
          {
            'R1_Op_30_Pos_Afuera': RDK_R1_OP_30_Pos_Afuera,
            'R1_Op_30_Pos_Dentro': RDK_R1_OP_30_Pos_Dentro,
            'R1_Op_30_Pos_X': RDK_R1_OP_30_Pos_X,
          },
        )

        robotR1.setPoseFrame(frameR1_OP_30_runtime)
        robotR1.setSpeed(R1_OP_30_LINEAR_SPEED_MM_S, R1_OP_30_JOINT_SPEED_DEG_S)
        robotR1.setRounding(0)

        print(f"Movimientos Robot 1 - Operación Op_30_{OP_30_OPERATION_OPTION}")
        run_timed_block(
          f'Operación Op_30_{OP_30_OPERATION_OPTION}',
          RDK,
          timer,
          section_times,
          lambda: (
            execute_robot_step_with_speed(robotR1, f'R1 -> Op_30_{OP_30_OPERATION_OPTION}_Pos_Afuera (MoveJ)', 'J', RDK_R1_OP_30_Pos_Afuera, R1_OP_30_LINEAR_SPEED_MM_S, R1_OP_30_JOINT_SPEED_DEG_S),
            execute_robot_step_with_speed(robotR1, f'R1 -> Op_30_{OP_30_OPERATION_OPTION}_Pos_Dentro (MoveL)', 'L', RDK_R1_OP_30_Pos_Dentro, R1_OP_30_LINEAR_SPEED_MM_S, R1_OP_30_JOINT_SPEED_DEG_S),
            execute_robot_step_with_speed(robotR1, f'R1 -> Op_30_{OP_30_OPERATION_OPTION}_Pos_X (MoveL)', 'L', RDK_R1_OP_30_Pos_X, R1_OP_30_X_LINEAR_SPEED_MM_S, R1_OP_30_X_JOINT_SPEED_DEG_S),
            execute_dwell(f'Op_30_{OP_30_OPERATION_OPTION} Pos_X', R1_OP_30_X_DWELL_S),
            execute_robot_step_with_speed(robotR1, f'R1 -> Op_30_{OP_30_OPERATION_OPTION}_Pos_Afuera (MoveL)', 'L', RDK_R1_OP_30_Pos_Afuera, R1_OP_30_LINEAR_SPEED_MM_S, R1_OP_30_JOINT_SPEED_DEG_S),
          ),
        )
      elif RUN_OP_30_SEQUENCE:
        print(f"Secuencia Op_30_{OP_30_OPERATION_OPTION} omitida: faltan frame/targets en esta operación.")

      if RUN_OP_50_SEQUENCE and sequence_op_50_items_found:
        robotR1.setPoseFrame(frameR1_OP_50)
        robotR1.setSpeed(R1_OP_50_LINEAR_SPEED_MM_S, R1_OP_50_JOINT_SPEED_DEG_S)
        robotR1.setRounding(0)

        print("Movimientos Robot 1 - Operación Op_50")
        run_timed_block(
          'Operación Op_50',
          RDK,
          timer,
          section_times,
          lambda: (
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_50_Pos_Afuera (MoveJ)', 'J', RDK_R1_OP_50_Pos_Afuera, R1_OP_50_LINEAR_SPEED_MM_S, R1_OP_50_JOINT_SPEED_DEG_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_50_Pos_Dentro (MoveL)', 'L', RDK_R1_OP_50_Pos_Dentro, R1_OP_50_LINEAR_SPEED_MM_S, R1_OP_50_JOINT_SPEED_DEG_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_50_Pos_X (MoveL)', 'L', RDK_R1_OP_50_Pos_X, R1_OP_50_X_LINEAR_SPEED_MM_S, R1_OP_50_X_JOINT_SPEED_DEG_S),
            execute_dwell('Op_50 Pos_X', R1_OP_50_X_DWELL_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_50_Pos_Afuera (MoveL)', 'L', RDK_R1_OP_50_Pos_Afuera, R1_OP_50_LINEAR_SPEED_MM_S, R1_OP_50_JOINT_SPEED_DEG_S),
          ),
        )
      elif RUN_OP_50_SEQUENCE:
        print("Secuencia Op_50 omitida: faltan frame/targets en esta operación.")

      if RUN_OP_60_SEQUENCE and sequence_op_60_items_found:
        robotR1.setPoseFrame(frameR1_OP_60)
        robotR1.setSpeed(R1_OP_60_LINEAR_SPEED_MM_S, R1_OP_60_JOINT_SPEED_DEG_S)
        robotR1.setRounding(0)

        print("Movimientos Robot 1 - Operación Op_60")
        run_timed_block(
          'Operación Op_60',
          RDK,
          timer,
          section_times,
          lambda: (
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_60_Pos_Afuera (MoveJ)', 'J', RDK_R1_OP_60_Pos_Afuera, R1_OP_60_LINEAR_SPEED_MM_S, R1_OP_60_JOINT_SPEED_DEG_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_60_Pos_Dentro (MoveL)', 'L', RDK_R1_OP_60_Pos_Dentro, R1_OP_60_LINEAR_SPEED_MM_S, R1_OP_60_JOINT_SPEED_DEG_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_60_Pos_X (MoveL)', 'L', RDK_R1_OP_60_Pos_X, R1_OP_60_X_LINEAR_SPEED_MM_S, R1_OP_60_X_JOINT_SPEED_DEG_S),
            execute_dwell('Op_60 Pos_X', R1_OP_60_X_DWELL_S),
            execute_robot_step_with_speed(robotR1, 'R1 -> Op_60_Pos_Afuera (MoveL)', 'L', RDK_R1_OP_60_Pos_Afuera, R1_OP_60_LINEAR_SPEED_MM_S, R1_OP_60_JOINT_SPEED_DEG_S),
          ),
        )
      elif RUN_OP_60_SEQUENCE:
        print("Secuencia Op_60 omitida: faltan frame/targets en esta operación.")

      if RUN_OP_70_SEQUENCE and sequence_op_70_items_found:
        robotR1.setPoseFrame(frameR1_OP_70)
        robotR1.setSpeed(R1_OP_70_LINEAR_SPEED_MM_S, R1_OP_70_JOINT_SPEED_DEG_S)
        robotR1.setRounding(0)

        if RUN_R2_SEQUENCE_FROM_OP70 and sequence_r2_items_found:
          if r2_sequence_state['error'] is not None:
            raise Exception(f"Error en secuencia R2 desde Op_70: {r2_sequence_state['error']}")

          running_thread = r2_sequence_state['thread']
          if running_thread is not None and running_thread.is_alive():
            print("R1 llegó a Op_70 y espera: R2 aún ejecuta Op_70.")
            wait_r1_start = timer()
            while running_thread.is_alive():
              if r2_sequence_state['error'] is not None:
                raise Exception(f"Error en secuencia R2 desde Op_70: {r2_sequence_state['error']}")
              if (timer() - wait_r1_start) > OP70_HANDSHAKE_TIMEOUT_S:
                raise Exception(
                  "Timeout de control Op_70: R1 esperó a que R2 liberara Op_70."
                )
              time.sleep(OP70_HANDSHAKE_POLL_S)
            r2_sequence_state['thread'] = None

          print("Movimientos Robot 1 - Operación Op_70 (controlado)")
          execute_robot_step_with_speed(robotR1, 'R1 -> Op_70_Pos_Afuera (MoveJ)', 'J', RDK_R1_OP_70_Pos_Afuera, R1_OP_70_LINEAR_SPEED_MM_S, R1_OP_70_JOINT_SPEED_DEG_S)
          execute_robot_step_with_speed(robotR1, 'R1 -> Op_70_Pos_Dentro (MoveL)', 'L', RDK_R1_OP_70_Pos_Dentro, R1_OP_70_LINEAR_SPEED_MM_S, R1_OP_70_JOINT_SPEED_DEG_S)
          execute_robot_step_with_speed(robotR1, 'R1 -> Op_70_Pos_X (MoveL)', 'L', RDK_R1_OP_70_Pos_X, R1_OP_70_X_LINEAR_SPEED_MM_S, R1_OP_70_X_JOINT_SPEED_DEG_S)
          execute_dwell('Op_70 Pos_X', R1_OP_70_X_DWELL_S)
          execute_robot_step_with_speed(robotR1, 'R1 -> Op_70_Pos_Afuera (MoveL)', 'L', RDK_R1_OP_70_Pos_Afuera, R1_OP_70_LINEAR_SPEED_MM_S, R1_OP_70_JOINT_SPEED_DEG_S)

          r2_operation_sequence = [
            {
              'op_name': 'Op_70',
              'frame': frameR2_OP_70,
              'target_afuera': RDK_R2_OP_70_Pos_Afuera,
              'target_dentro': RDK_R2_OP_70_Pos_Dentro,
              'target_x': RDK_R2_OP_70_Pos_X,
              'linear_speed_mm_s': R2_OP_70_LINEAR_SPEED_MM_S,
              'joint_speed_deg_s': R2_OP_70_JOINT_SPEED_DEG_S,
              'x_linear_speed_mm_s': R2_OP_70_X_LINEAR_SPEED_MM_S,
              'x_joint_speed_deg_s': R2_OP_70_X_JOINT_SPEED_DEG_S,
              'x_dwell_s': R2_OP_70_X_DWELL_S,
            },
            {
              'op_name': 'Op_80',
              'frame': frameR2_OP_80,
              'target_afuera': RDK_R2_OP_80_Pos_Afuera,
              'target_dentro': RDK_R2_OP_80_Pos_Dentro,
              'target_x': RDK_R2_OP_80_Pos_X,
              'linear_speed_mm_s': R2_OP_80_LINEAR_SPEED_MM_S,
              'joint_speed_deg_s': R2_OP_80_JOINT_SPEED_DEG_S,
              'x_linear_speed_mm_s': R2_OP_80_X_LINEAR_SPEED_MM_S,
              'x_joint_speed_deg_s': R2_OP_80_X_JOINT_SPEED_DEG_S,
              'x_dwell_s': R2_OP_80_X_DWELL_S,
            },
            {
              'op_name': 'Op_90',
              'frame': frameR2_OP_90,
              'target_afuera': RDK_R2_OP_90_Pos_Afuera,
              'target_dentro': RDK_R2_OP_90_Pos_Dentro,
              'target_x': RDK_R2_OP_90_Pos_X,
              'linear_speed_mm_s': R2_OP_90_LINEAR_SPEED_MM_S,
              'joint_speed_deg_s': R2_OP_90_JOINT_SPEED_DEG_S,
              'x_linear_speed_mm_s': R2_OP_90_X_LINEAR_SPEED_MM_S,
              'x_joint_speed_deg_s': R2_OP_90_X_JOINT_SPEED_DEG_S,
              'x_dwell_s': R2_OP_90_X_DWELL_S,
            },
            {
              'op_name': 'Op_100',
              'frame': frameR2_OP_100,
              'target_afuera': RDK_R2_OP_100_Pos_Afuera,
              'target_dentro': RDK_R2_OP_100_Pos_Dentro,
              'target_x': RDK_R2_OP_100_Pos_X,
              'linear_speed_mm_s': R2_OP_100_LINEAR_SPEED_MM_S,
              'joint_speed_deg_s': R2_OP_100_JOINT_SPEED_DEG_S,
              'x_linear_speed_mm_s': R2_OP_100_X_LINEAR_SPEED_MM_S,
              'x_joint_speed_deg_s': R2_OP_100_X_JOINT_SPEED_DEG_S,
              'x_dwell_s': R2_OP_100_X_DWELL_S,
            },
            {
              'op_name': 'Op_110',
              'frame': frameR2_OP_110,
              'target_afuera': RDK_R2_OP_110_Pos_Afuera,
              'target_dentro': RDK_R2_OP_110_Pos_Dentro,
              'target_x': RDK_R2_OP_110_Pos_X,
              'linear_speed_mm_s': R2_OP_110_LINEAR_SPEED_MM_S,
              'joint_speed_deg_s': R2_OP_110_JOINT_SPEED_DEG_S,
              'x_linear_speed_mm_s': R2_OP_110_X_LINEAR_SPEED_MM_S,
              'x_joint_speed_deg_s': R2_OP_110_X_JOINT_SPEED_DEG_S,
              'x_dwell_s': R2_OP_110_X_DWELL_S,
            },
            {
              'op_name': 'Op_120',
              'frame': frameR2_OP_120,
              'target_afuera': RDK_R2_OP_120_Pos_Afuera,
              'target_dentro': RDK_R2_OP_120_Pos_Dentro,
              'target_x': RDK_R2_OP_120_Pos_X,
              'linear_speed_mm_s': R2_OP_120_LINEAR_SPEED_MM_S,
              'joint_speed_deg_s': R2_OP_120_JOINT_SPEED_DEG_S,
              'x_linear_speed_mm_s': R2_OP_120_X_LINEAR_SPEED_MM_S,
              'x_joint_speed_deg_s': R2_OP_120_X_JOINT_SPEED_DEG_S,
              'x_dwell_s': R2_OP_120_X_DWELL_S,
            },
            {
              'op_name': 'Op_130',
              'frame': frameR2_OP_130,
              'target_afuera': RDK_R2_OP_130_Pos_Afuera,
              'target_dentro': RDK_R2_OP_130_Pos_Dentro,
              'target_x': RDK_R2_OP_130_Pos_X,
              'linear_speed_mm_s': R2_OP_130_LINEAR_SPEED_MM_S,
              'joint_speed_deg_s': R2_OP_130_JOINT_SPEED_DEG_S,
              'x_linear_speed_mm_s': R2_OP_130_X_LINEAR_SPEED_MM_S,
              'x_joint_speed_deg_s': R2_OP_130_X_JOINT_SPEED_DEG_S,
              'x_dwell_s': R2_OP_130_X_DWELL_S,
            },
            {
              'op_name': 'Op_140',
              'frame': frameR2_OP_140,
              'target_afuera': RDK_R2_OP_140_Pos_Afuera,
              'target_dentro': RDK_R2_OP_140_Pos_Dentro,
              'target_x': RDK_R2_OP_140_Pos_X,
              'linear_speed_mm_s': R2_OP_140_LINEAR_SPEED_MM_S,
              'joint_speed_deg_s': R2_OP_140_JOINT_SPEED_DEG_S,
              'x_linear_speed_mm_s': R2_OP_140_X_LINEAR_SPEED_MM_S,
              'x_joint_speed_deg_s': R2_OP_140_X_JOINT_SPEED_DEG_S,
              'x_dwell_s': R2_OP_140_X_DWELL_S,
            },
          ]

          if RUN_R2_NOK_SEQUENCE:
            if sequence_r2_nok_items_found:
              r2_operation_sequence.append({
                'op_name': 'Nok',
                'frame': frameR2_NOK,
                'target_afuera': RDK_R2_NOK_Pos_Afuera,
                'target_dentro': RDK_R2_NOK_Pos_Dentro,
                'target_x': RDK_R2_NOK_Pos_X,
                'linear_speed_mm_s': R2_NOK_LINEAR_SPEED_MM_S,
                'joint_speed_deg_s': R2_NOK_JOINT_SPEED_DEG_S,
                'x_linear_speed_mm_s': R2_NOK_X_LINEAR_SPEED_MM_S,
                'x_joint_speed_deg_s': R2_NOK_X_JOINT_SPEED_DEG_S,
                'x_dwell_s': R2_NOK_X_DWELL_S,
              })
            else:
              print("Secuencia opcional R2_Nok omitida: faltan frame/targets.")

          r2_sequence_state['dispatched_cycles'] = r2_sequence_state['dispatched_cycles'] + 1
          if RUN_R2_IN_BACKGROUND:
            print(
              f"Despachando secuencia R2 desde Op_70 en segundo plano (ciclo {r2_sequence_state['dispatched_cycles']})."
            )
            r2_thread = threading.Thread(
              target=execute_r2_operations_sequence_worker,
              args=(
                r2_sequence_state,
                robotR2,
                r2_operation_sequence,
              ),
              daemon=True,
            )
            r2_sequence_state['thread'] = r2_thread
            r2_thread.start()
          else:
            print(
              f"Ejecutando secuencia R2 desde Op_70 en primer plano (ciclo {r2_sequence_state['dispatched_cycles']})."
            )
            r2_sequence_state['thread'] = None
            execute_r2_operations_sequence_worker(
              r2_sequence_state,
              robotR2,
              r2_operation_sequence,
            )
        else:
          if RUN_R2_SEQUENCE_FROM_OP70:
            print("Secuencia R2 desde Op_70 omitida: faltan frame/targets de R2. Se ejecuta Op_70 solo con R1.")

          print("Movimientos Robot 1 - Operación Op_70")
          run_timed_block(
            'Operación Op_70',
            RDK,
            timer,
            section_times,
            lambda: (
              execute_robot_step_with_speed(robotR1, 'R1 -> Op_70_Pos_Afuera (MoveJ)', 'J', RDK_R1_OP_70_Pos_Afuera, R1_OP_70_LINEAR_SPEED_MM_S, R1_OP_70_JOINT_SPEED_DEG_S),
              execute_robot_step_with_speed(robotR1, 'R1 -> Op_70_Pos_Dentro (MoveL)', 'L', RDK_R1_OP_70_Pos_Dentro, R1_OP_70_LINEAR_SPEED_MM_S, R1_OP_70_JOINT_SPEED_DEG_S),
              execute_robot_step_with_speed(robotR1, 'R1 -> Op_70_Pos_X (MoveL)', 'L', RDK_R1_OP_70_Pos_X, R1_OP_70_X_LINEAR_SPEED_MM_S, R1_OP_70_X_JOINT_SPEED_DEG_S),
              execute_dwell('Op_70 Pos_X', R1_OP_70_X_DWELL_S),
              execute_robot_step_with_speed(robotR1, 'R1 -> Op_70_Pos_Afuera (MoveL)', 'L', RDK_R1_OP_70_Pos_Afuera, R1_OP_70_LINEAR_SPEED_MM_S, R1_OP_70_JOINT_SPEED_DEG_S),
            ),
          )
      elif RUN_OP_70_SEQUENCE:
        print("Secuencia Op_70 omitida: faltan frame/targets en esta operación.")

      if R1_SEQUENCE_CYCLES > 0 and cycle_number >= R1_SEQUENCE_CYCLES:
        break
  elif run_ops_sequences:
    print("Secuencia Op_00 omitida: faltan frame/targets en esta operación.")
  else:
    print("Modo HOME_ONLY: secuencias Op no ejecutadas.")

  if run_ops_sequences and RUN_NOK_SEQUENCE and sequence_nok_items_found:
    robotR1.setPoseFrame(frameR1_NOK)
    robotR1.setSpeed(R1_NOK_LINEAR_SPEED_MM_S, R1_NOK_JOINT_SPEED_DEG_S)
    robotR1.setRounding(0)

    print("Movimientos Robot 1 - Secuencia NOK (separada)")
    run_timed_block(
      'Secuencia NOK',
      RDK,
      timer,
      section_times,
      lambda: (
        execute_robot_step_with_speed(robotR1, 'R1 -> NOK_Pos_Afuera (MoveJ)', 'J', RDK_R1_NOK_Pos_Afuera, R1_NOK_LINEAR_SPEED_MM_S, R1_NOK_JOINT_SPEED_DEG_S),
        execute_robot_step_with_speed(robotR1, 'R1 -> NOK_Pos_Dentro (MoveL)', 'L', RDK_R1_NOK_Pos_Dentro, R1_NOK_LINEAR_SPEED_MM_S, R1_NOK_JOINT_SPEED_DEG_S),
        execute_robot_step_with_speed(robotR1, 'R1 -> NOK_Pos_X (MoveL)', 'L', RDK_R1_NOK_Pos_X, R1_NOK_X_LINEAR_SPEED_MM_S, R1_NOK_X_JOINT_SPEED_DEG_S),
        execute_dwell('NOK Pos_X', R1_NOK_X_DWELL_S),
        execute_robot_step_with_speed(robotR1, 'R1 -> NOK_Pos_Afuera (MoveL)', 'L', RDK_R1_NOK_Pos_Afuera, R1_NOK_LINEAR_SPEED_MM_S, R1_NOK_JOINT_SPEED_DEG_S),
      ),
    )
  elif run_ops_sequences and RUN_NOK_SEQUENCE:
    print("Secuencia NOK omitida: faltan frame/targets en esta operación.")

  if FORCE_VISIBLE_TEST_MOVE and EXECUTION_MODE == 'HOME_ONLY':
    do_visible_test_move(robotR1, 'R1', joint_index=0, delta_deg=10.0)
    do_visible_test_move(robotR2, 'R2', joint_index=0, delta_deg=10.0)

  if run_ops_sequences and RUN_R2_SEQUENCE_FROM_OP70 and sequence_r2_items_found:
    running_thread = r2_sequence_state.get('thread')
    if running_thread is not None and running_thread.is_alive():
      print("Esperando fin de secuencia R2 desde Op_70 antes de cerrar ejecución...")
      wait_close_start = timer()
      while running_thread.is_alive():
        if r2_sequence_state.get('error') is not None:
          raise Exception(f"Error en secuencia R2 desde Op_70: {r2_sequence_state['error']}")
        if (timer() - wait_close_start) > OP70_HANDSHAKE_TIMEOUT_S:
          raise Exception("Timeout al cerrar: R2 no terminó la secuencia desde Op_70 en el tiempo esperado.")
        time.sleep(OP70_HANDSHAKE_POLL_S)

    if r2_sequence_state.get('error') is not None:
      raise Exception(f"Error en secuencia R2 desde Op_70: {r2_sequence_state['error']}")

  print(f"Juntas finales R1: {robotR1.Joints().list()}")
  print(f"Juntas finales R2: {robotR2.Joints().list()}")

  frame_snapshots_after = {
    frame_name: get_pose_snapshot(frame_item)
    for frame_name, frame_item in monitored_frames.items()
  }
  print_frame_stability_report(frame_snapshots_before, frame_snapshots_after)
  changed_frames = get_changed_frame_names(frame_snapshots_before, frame_snapshots_after)
  if changed_frames:
    raise Exception(f"Se detectó movimiento no permitido de frames de operación: {changed_frames}")

  total_robodk_end = get_robodk_sim_time(RDK)
  total_robodk_seconds = None
  if total_robodk_start is not None and total_robodk_end is not None:
    total_robodk_seconds = total_robodk_end - total_robodk_start

  current_total_python = timer() - start_time
  print_timing_summary(section_times, current_total_python, total_robodk_seconds)
  if EXPORT_TIMES_CSV:
    export_timing_summary_csv(section_times, current_total_python, total_robodk_seconds, TIMES_CSV_FILE)
except Exception as error:
  print(f"Error en comunicación/ejecución con RoboDK: {error}")
  raise





end_time = timer()
print(f"Tiempo de ejecucion: {end_time - start_time:.6f} segundos")
