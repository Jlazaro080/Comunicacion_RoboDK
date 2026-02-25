import time
import sys
import difflib
import csv
import os
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
OP_30_OPERATION_OPTION = os.getenv('OP30_OPTION', 'B').strip().upper()  # Opciones: 'A', 'B'
MONITOR_ONLY_ACTIVE_OP30_FRAME = True
FORCE_VISIBLE_TEST_MOVE = False
R1_OP_00_LINEAR_SPEED_MM_S = 300
R1_OP_00_JOINT_SPEED_DEG_S = 250
R1_OP_00_X_LINEAR_SPEED_MM_S = 60
R1_OP_00_X_JOINT_SPEED_DEG_S = 180
R1_OP_00_X_DWELL_S = 1.0
R1_OP_10_LINEAR_SPEED_MM_S = 300
R1_OP_10_JOINT_SPEED_DEG_S = 250
R1_OP_10_X_LINEAR_SPEED_MM_S = 35
R1_OP_10_X_JOINT_SPEED_DEG_S = 120
R1_OP_10_X_DWELL_S = 1.0
R1_OP_20_LINEAR_SPEED_MM_S = 300
R1_OP_20_JOINT_SPEED_DEG_S = 250
R1_OP_20_X_LINEAR_SPEED_MM_S = 35
R1_OP_20_X_JOINT_SPEED_DEG_S = 120
R1_OP_20_X_DWELL_S = 1.0
R1_OP_30_LINEAR_SPEED_MM_S = 300
R1_OP_30_JOINT_SPEED_DEG_S = 250
R1_OP_30_X_LINEAR_SPEED_MM_S = 35
R1_OP_30_X_JOINT_SPEED_DEG_S = 120
R1_OP_30_X_DWELL_S = 1.0
R1_OP_50_LINEAR_SPEED_MM_S = 300
R1_OP_50_JOINT_SPEED_DEG_S = 250
R1_OP_50_X_LINEAR_SPEED_MM_S = 35
R1_OP_50_X_JOINT_SPEED_DEG_S = 120
R1_OP_50_X_DWELL_S = 1.0
R1_OP_60_LINEAR_SPEED_MM_S = 300
R1_OP_60_JOINT_SPEED_DEG_S = 250
R1_OP_60_X_LINEAR_SPEED_MM_S = 35
R1_OP_60_X_JOINT_SPEED_DEG_S = 120
R1_OP_60_X_DWELL_S = 1.0
R1_OP_70_LINEAR_SPEED_MM_S = 300
R1_OP_70_JOINT_SPEED_DEG_S = 250
R1_OP_70_X_LINEAR_SPEED_MM_S = 35
R1_OP_70_X_JOINT_SPEED_DEG_S = 120
R1_OP_70_X_DWELL_S = 1.0
R1_NOK_LINEAR_SPEED_MM_S = 300
R1_NOK_JOINT_SPEED_DEG_S = 250
R1_NOK_X_LINEAR_SPEED_MM_S = 35
R1_NOK_X_JOINT_SPEED_DEG_S = 120
R1_NOK_X_DWELL_S = 1.0
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
  robot.setSpeed(linear_speed_mm_s, joint_speed_deg_s)
  execute_robot_step(robot, step_name, move_type, target)


def execute_dwell(label, dwell_seconds):
  if dwell_seconds <= 0:
    return
  print(f"Pausa en {label}: {dwell_seconds:.2f}s")
  time.sleep(dwell_seconds)


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

if run_ops_sequences and RUN_NOK_SEQUENCE and STRICT_NOK_REQUIRED and not sequence_nok_items_found:
  raise Exception(f"Secuencia NOK estricta: faltan elementos NOK: {missing_nok_items}")

try:
  section_times = {}
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

  robotR1.setSpeed(1, 50)
  run_timed_block(
    'Home R1',
    RDK,
    timer,
    section_times,
    lambda: move_robot_to_home(robotR1, 'R1', RDK_R1_Home_General),
  )

  robotR2.setSpeed(10, 50)
  run_timed_block(
    'Home R2',
    RDK,
    timer,
    section_times,
    lambda: move_robot_to_home(robotR2, 'R2', RDK_R2_Home_General),
  )

  if run_ops_sequences and sequence_op_00_items_found:
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
