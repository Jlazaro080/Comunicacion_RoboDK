import time
import sys
import difflib
import csv
from datetime import datetime
from robodk import robolink


EXECUTION_MODE = 'HOME_PLUS_E01'  # Opciones: 'HOME_ONLY', 'HOME_PLUS_E01'
STRICT_E01_REQUIRED = False   # Solo aplica en HOME_PLUS_E01
RUN_E02_SEQUENCE = True
STRICT_E02_REQUIRED = False
FORCE_VISIBLE_TEST_MOVE = False
R1_E01_LINEAR_SPEED_MM_S = 100
R1_E01_JOINT_SPEED_DEG_S = 250
R1_E01_X_LINEAR_SPEED_MM_S = 60
R1_E01_X_JOINT_SPEED_DEG_S = 180
R1_E01_X_DWELL_S = 5.0
R1_E02_LINEAR_SPEED_MM_S = 100
R1_E02_JOINT_SPEED_DEG_S = 250
R1_E02_X_LINEAR_SPEED_MM_S = 35
R1_E02_X_JOINT_SPEED_DEG_S = 120
R1_E02_X_DWELL_S = 1.0
EXPORT_TIMES_CSV = True
TIMES_CSV_FILE = 'tiempos_robodk.csv'


def list_station_item_names(rdk):
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

  item_names = list_station_item_names(rdk)
  if not item_names:
    print("No se pudo recuperar el listado de items de la estación.")
    return

  suggestions = difflib.get_close_matches(missing_name, item_names, n=8, cutoff=0.5)
  if suggestions:
    print("Sugerencias de nombres parecidos:")
    for suggestion in suggestions:
      print(f"  - {suggestion}")
  else:
    print("No encontré coincidencias cercanas para ese nombre.")

  max_items_to_print = 80
  print(f"Items disponibles en la estación (mostrando hasta {max_items_to_print}):")
  for item_name in item_names[:max_items_to_print]:
    print(f"  - {item_name}")

  hidden_items = len(item_names) - max_items_to_print
  if hidden_items > 0:
    print(f"  ... y {hidden_items} item(s) más.")


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

# Posiciones opcionales de Robot 1 (según estación)
frameR1 = get_first_valid_optional(RDK, ['R1_E01'])
frameBase = get_first_valid_optional(RDK, ['R1_Base'])
RDK_R1_E01_Pos_Dentro = get_first_valid_optional(RDK, ['R1_E01_Pos_Dentro'])
RDK_R1_E01_Pos_X = get_first_valid_optional(RDK, ['R1_E01_Pos_X'])
RDK_R1_E01_Pos_Afuera = get_first_valid_optional(RDK, ['R1_E01_Pos_Afuera'])

frameR1_E02 = get_first_valid_optional(RDK, ['R1_E02'])
RDK_R1_E02_Pos_Dentro = get_first_valid_optional(RDK, ['R1_E02_Pos_Dentro'])
RDK_R1_E02_Pos_X = get_first_valid_optional(RDK, ['R1_E02_Pos_X'])
RDK_R1_E02_Pos_Afuera = get_first_valid_optional(RDK, ['R1_E02_Pos_Afuera'])

e01_required_items = {
  'R1_E01': frameR1,
  'R1_E01_Pos_Dentro': RDK_R1_E01_Pos_Dentro,
  'R1_E01_Pos_X': RDK_R1_E01_Pos_X,
  'R1_E01_Pos_Afuera': RDK_R1_E01_Pos_Afuera,
}

missing_e01_items = [name for name, value in e01_required_items.items() if value is None]

sequence_items_found = all([
  frameR1 is not None,
  RDK_R1_E01_Pos_Dentro is not None,
  RDK_R1_E01_Pos_X is not None,
  RDK_R1_E01_Pos_Afuera is not None
])

e02_required_items = {
  'R1_E02': frameR1_E02,
  'R1_E02_Pos_Dentro': RDK_R1_E02_Pos_Dentro,
  'R1_E02_Pos_X': RDK_R1_E02_Pos_X,
  'R1_E02_Pos_Afuera': RDK_R1_E02_Pos_Afuera,
}

missing_e02_items = [name for name, value in e02_required_items.items() if value is None]

sequence_e02_items_found = all([
  frameR1_E02 is not None,
  RDK_R1_E02_Pos_Dentro is not None,
  RDK_R1_E02_Pos_X is not None,
  RDK_R1_E02_Pos_Afuera is not None
])

if EXECUTION_MODE not in ('HOME_ONLY', 'HOME_PLUS_E01'):
  raise Exception("EXECUTION_MODE inválido. Usa 'HOME_ONLY' o 'HOME_PLUS_E01'.")

if EXECUTION_MODE == 'HOME_PLUS_E01':
  if missing_e01_items:
    print("Elementos faltantes para secuencia E01:")
    for missing_item in missing_e01_items:
      print(f"  - {missing_item}")
  else:
    print("Secuencia E01 lista: todos los elementos requeridos están disponibles.")

  if RUN_E02_SEQUENCE:
    if missing_e02_items:
      print("Elementos faltantes para secuencia E02:")
      for missing_item in missing_e02_items:
        print(f"  - {missing_item}")
    else:
      print("Secuencia E02 lista: todos los elementos requeridos están disponibles.")

if EXECUTION_MODE == 'HOME_PLUS_E01' and STRICT_E01_REQUIRED and not sequence_items_found:
  raise Exception(f"Modo HOME_PLUS_E01 estricto: faltan elementos E01: {missing_e01_items}")

if EXECUTION_MODE == 'HOME_PLUS_E01' and RUN_E02_SEQUENCE and STRICT_E02_REQUIRED and not sequence_e02_items_found:
  raise Exception(f"Secuencia E02 estricta: faltan elementos E02: {missing_e02_items}")

try:
  section_times = {}
  total_robodk_start = get_robodk_sim_time(RDK)

  if frameBase is not None:
    robotR1.setPoseFrame(frameBase.Pose())

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

  if EXECUTION_MODE == 'HOME_PLUS_E01' and sequence_items_found:
    #############################Movimientos Robot 1
    robotR1.setPoseFrame(frameR1.Pose())
    robotR1.setSpeed(R1_E01_LINEAR_SPEED_MM_S, R1_E01_JOINT_SPEED_DEG_S)
    robotR1.setRounding(0)

    print("Movimientos Robot 1")
    run_timed_block(
      'Estación E01',
      RDK,
      timer,
      section_times,
      lambda: (
        execute_robot_step_with_speed(robotR1, 'R1 -> E01_Pos_Afuera (MoveJ)', 'J', RDK_R1_E01_Pos_Afuera, R1_E01_LINEAR_SPEED_MM_S, R1_E01_JOINT_SPEED_DEG_S),
        execute_robot_step_with_speed(robotR1, 'R1 -> E01_Pos_Dentro (MoveL)', 'L', RDK_R1_E01_Pos_Dentro, R1_E01_LINEAR_SPEED_MM_S, R1_E01_JOINT_SPEED_DEG_S),
        execute_robot_step_with_speed(robotR1, 'R1 -> E01_Pos_X (MoveL)', 'L', RDK_R1_E01_Pos_X, R1_E01_X_LINEAR_SPEED_MM_S, R1_E01_X_JOINT_SPEED_DEG_S),
        execute_dwell('E01 Pos_X', R1_E01_X_DWELL_S),
        execute_robot_step_with_speed(robotR1, 'R1 -> E01_Pos_Afuera (MoveL)', 'L', RDK_R1_E01_Pos_Afuera, R1_E01_LINEAR_SPEED_MM_S, R1_E01_JOINT_SPEED_DEG_S),
      ),
    )

    if RUN_E02_SEQUENCE and sequence_e02_items_found:
      robotR1.setPoseFrame(frameR1_E02.Pose())
      robotR1.setSpeed(R1_E02_LINEAR_SPEED_MM_S, R1_E02_JOINT_SPEED_DEG_S)
      robotR1.setRounding(0)

      print("Movimientos Robot 1 - Estación E02")
      run_timed_block(
        'Estación E02',
        RDK,
        timer,
        section_times,
        lambda: (
          execute_robot_step_with_speed(robotR1, 'R1 -> E02_Pos_Afuera (MoveJ)', 'J', RDK_R1_E02_Pos_Afuera, R1_E02_LINEAR_SPEED_MM_S, R1_E02_JOINT_SPEED_DEG_S),
          execute_robot_step_with_speed(robotR1, 'R1 -> E02_Pos_Dentro (MoveL)', 'L', RDK_R1_E02_Pos_Dentro, R1_E02_LINEAR_SPEED_MM_S, R1_E02_JOINT_SPEED_DEG_S),
          execute_robot_step_with_speed(robotR1, 'R1 -> E02_Pos_X (MoveL)', 'L', RDK_R1_E02_Pos_X, R1_E02_X_LINEAR_SPEED_MM_S, R1_E02_X_JOINT_SPEED_DEG_S),
          execute_dwell('E02 Pos_X', R1_E02_X_DWELL_S),
          execute_robot_step_with_speed(robotR1, 'R1 -> E02_Pos_Afuera (MoveL)', 'L', RDK_R1_E02_Pos_Afuera, R1_E02_LINEAR_SPEED_MM_S, R1_E02_JOINT_SPEED_DEG_S),
        ),
      )
    elif RUN_E02_SEQUENCE:
      print("Secuencia E02 omitida: faltan frame/targets en esta estación.")
  elif EXECUTION_MODE == 'HOME_PLUS_E01':
    print("Secuencia E01 omitida: faltan frame/targets en esta estación.")
  else:
    print("Modo HOME_ONLY: secuencia E01 no ejecutada.")

  if FORCE_VISIBLE_TEST_MOVE and EXECUTION_MODE == 'HOME_ONLY':
    do_visible_test_move(robotR1, 'R1', joint_index=0, delta_deg=10.0)
    do_visible_test_move(robotR2, 'R2', joint_index=0, delta_deg=10.0)

  print(f"Juntas finales R1: {robotR1.Joints().list()}")
  print(f"Juntas finales R2: {robotR2.Joints().list()}")

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
