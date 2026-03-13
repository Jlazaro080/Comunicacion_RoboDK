# Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html
# Note: It is not required to keep a copy of this file, your Python script is saved with your RDK project

# You can also use the new version of the API:
import sys
import time

try:
  from robodk.robolink import (
    ITEM_TYPE_FRAME,
    ITEM_TYPE_ROBOT,
    ITEM_TYPE_TARGET,
    Robolink,
  )
  from robodk.robomath import pause
except ImportError as exc:
  raise ImportError(
    "No se pudo importar la API de RoboDK. Instala 'robodk' con `pip install robodk` "
    "o ejecuta el script desde el entorno de Python integrado de RoboDK."
  ) from exc


if sys.gettrace() is None:
  timer = time.time
else:
  timer = time.perf_counter()


start_time = timer()

# Link to RoboDK
RDK = Robolink()


def get_required_item(name, item_type=ITEM_TYPE_TARGET):
  item = RDK.Item(name, item_type)
  if not item.Valid():
    raise Exception(f"No se encontro el item requerido: {name}")
  return item


def get_required_item_any(names, item_type=ITEM_TYPE_TARGET):
  for name in names:
    item = RDK.Item(name, item_type)
    if item.Valid():
      return item
  raise Exception(f"No se encontro ninguno de los items requeridos: {names}")


def get_optional_item_any(names, item_type=ITEM_TYPE_TARGET):
  for name in names:
    item = RDK.Item(name, item_type)
    if item.Valid():
      return item
  return None


def get_available_items(names, item_type=ITEM_TYPE_TARGET):
  items = []
  for name in names:
    item = RDK.Item(name, item_type)
    if item.Valid():
      items.append(item)
  if not items:
    raise Exception(f"No se encontro ninguno de los items requeridos: {names}")
  return items


def get_home_targets(robot_tag, preferred_names):
  # Prefer explicit names, then append any target containing both robot tag and "home".
  targets = []
  seen_names = set()

  for name in preferred_names:
    item = RDK.Item(name, ITEM_TYPE_TARGET)
    if item.Valid() and name not in seen_names:
      targets.append(item)
      seen_names.add(name)

  for item in RDK.ItemList(filter=ITEM_TYPE_TARGET):
    name = item.Name()
    lname = name.lower()
    if robot_tag.lower() in lname and "home" in lname and name not in seen_names:
      targets.append(item)
      seen_names.add(name)

  if not targets:
    raise Exception(
      f"No se encontraron targets Home para {robot_tag}."
    )

  return targets

#get the robot by name:
robotR1 = get_required_item('R1', ITEM_TYPE_ROBOT)
#get the robot by name:
robotR2 = get_required_item('R2', ITEM_TYPE_ROBOT)

# ===================== AJUSTE DE VELOCIDADES =====================
# Unidades RoboDK:
# - linear: mm/s
# - joints: deg/s
# - linear_accel: mm/s^2
# - joints_accel: deg/s^2
R1_SPEED_CONFIG = {
  "linear": 200,
  "joints": 50,
  "linear_accel": 600,
  "joints_accel": 200,
}

R2_SPEED_CONFIG = {
  "linear": 200,
  "joints": 50,
  "linear_accel": 600,
  "joints_accel": 200,
}


def apply_robot_speed(robot, robot_name, speed_config):
  try:
    robot.setSpeed(
      speed_config["linear"],
      speed_config["joints"],
      speed_config["linear_accel"],
      speed_config["joints_accel"]
    )
  except TypeError:
    robot.setSpeed(speed_config["linear"], speed_config["joints"])

  print(
    f"Velocidad {robot_name}: LIN={speed_config['linear']} mm/s, "
    f"JNT={speed_config['joints']} deg/s, "
    f"A_LIN={speed_config['linear_accel']} mm/s^2, "
    f"A_JNT={speed_config['joints_accel']} deg/s^2"
  )


apply_robot_speed(robotR1, "R1", R1_SPEED_CONFIG)
apply_robot_speed(robotR2, "R2", R2_SPEED_CONFIG)

R1_OPERATION_SPEEDS = {
  "default": {
    "travel": {"linear": 220, "joints": 60, "linear_accel": 700, "joints_accel": 220},
    "process": {"linear": 120, "joints": 35, "linear_accel": 400, "joints_accel": 150},
  },
}

R2_OPERATION_SPEEDS = {
  "default": {
    "travel": {"linear": 220, "joints": 60, "linear_accel": 700, "joints_accel": 220},
    "process": {"linear": 120, "joints": 35, "linear_accel": 400, "joints_accel": 150},
  },
}

R1_OPERATION_TIMES_SEC = {
  "default": 1.0,
  "OP_00": 1.0,
  "OP_10": 1.0,
  "OP_20": 1.0,
  "OP_30_A": 1.0,
  "OP_30_B": 1.0,
  "OP_50": 1.0,
  "OP_60": 1.0,
  "OP_70": 1.0,
}

R2_OPERATION_TIMES_SEC = {
  "default": 1.0,
  "OP_70": 1.0,
  "OP_80": 1.0,
  "OP_90": 1.0,
  "OP_100": 1.0,
  "OP_110": 1.0,
  "OP_120": 1.0,
  "OP_130": 1.0,
  "OP_140": 1.0,
}

# Si esta opcion esta activa, todos los desplazamientos del ciclo de operacion
# se ejecutan con MoveL para priorizar trayectorias lineales visibles.
FORCE_LINEAR_PROCESS_TRAJECTORY = True


def set_speed_from_cfg(robot, speed_cfg):
  try:
    robot.setSpeed(
      speed_cfg["linear"],
      speed_cfg["joints"],
      speed_cfg["linear_accel"],
      speed_cfg["joints_accel"],
    )
  except TypeError:
    robot.setSpeed(speed_cfg["linear"], speed_cfg["joints"])


def get_op_speed_cfg(speed_table, op_key):
  return speed_table.get(op_key, speed_table["default"])


def get_operation_time_sec(time_table, op_key):
  return float(time_table.get(op_key, time_table.get("default", 0.0)))


def hold_process_time(seconds, robot_name, op_key):
  if seconds <= 0:
    return

  print(f"[{robot_name} {op_key}] Tiempo de proceso: {seconds:.2f} s")
  try:
    pause(seconds)
  except Exception:
    time.sleep(seconds)


def wait_robot_motion(robot, robot_name, step_name, timeout_sec=120.0, poll_sec=0.1):
  start = timer()
  while robot.Busy():
    if timer() - start > timeout_sec:
      robot.Stop()
      raise TimeoutError(
        f"Movimiento {step_name} de {robot_name} excedio {timeout_sec:.1f}s"
      )
    time.sleep(poll_sec)


def move_with_timeout(robot, robot_name, move_kind, target, step_name, timeout_sec=120.0):
  if move_kind == "J":
    robot.MoveJ(target, False)
  else:
    robot.MoveL(target, False)
  wait_robot_motion(robot, robot_name, step_name, timeout_sec=timeout_sec)


def format_exception(exc):
  message = str(exc).strip()
  if message:
    return f"{type(exc).__name__}: {message}"
  return f"{type(exc).__name__}: {repr(exc)}"


def move_with_fallback(robot, robot_name, primary_kind, fallback_kind, target, step_name, timeout_sec=120.0):
  try:
    move_with_timeout(robot, robot_name, primary_kind, target, step_name, timeout_sec=timeout_sec)
  except Exception as primary_exc:
    if fallback_kind is None or fallback_kind == primary_kind:
      raise

    print(
      f"ADVERTENCIA: {step_name} fallo en Move{primary_kind}. "
      f"Reintentando Move{fallback_kind}. Detalle: {format_exception(primary_exc)}"
    )
    move_with_timeout(
      robot,
      robot_name,
      fallback_kind,
      target,
      f"{step_name}-Fallback-{fallback_kind}",
      timeout_sec=timeout_sec,
    )


def move_home_with_timeout(robot, robot_name, targets, base_frame=None, timeout_sec=45.0, poll_sec=0.1):
  target_list = targets if isinstance(targets, list) else [targets]
  print(f"Inicio Home General {robot_name}")

  if base_frame is not None:
    try:
      robot.setPoseFrame(base_frame)
      print(f"Frame base {robot_name}: {base_frame.Name()}")
    except Exception as exc:
      print(f"ADVERTENCIA: No se pudo configurar frame base de {robot_name}: {exc}")

  for idx, target in enumerate(target_list, start=1):
    target_name = target.Name()
    try:
      if len(target_list) > 1:
        print(f"Intento Home {robot_name} {idx}/{len(target_list)} con target: {target_name}")

      # Use non-blocking motion and poll Busy() to avoid indefinite WaitMove() hangs.
      robot.MoveJ(target, False)
      start = timer()
      while robot.Busy():
        if timer() - start > timeout_sec:
          robot.Stop()
          raise TimeoutError(
            f"Home {robot_name} excedio {timeout_sec:.1f}s en target {target_name}"
          )
        time.sleep(poll_sec)

      print(f"Fin de Home Robot {robot_name} con target: {target_name}")
      return True
    except Exception as exc:
      print(f"ADVERTENCIA: Fallo Home {robot_name} con target {target_name}: {exc}")

      # Fallback: try the target joint values directly with the same robot.
      try:
        home_joints = target.Joints().tolist()
        print(f"Intentando Home {robot_name} por juntas de target: {target_name}")
        robot.MoveJ(home_joints, False)
        start = timer()
        while robot.Busy():
          if timer() - start > timeout_sec:
            robot.Stop()
            raise TimeoutError(
              f"Home por juntas {robot_name} excedio {timeout_sec:.1f}s"
            )
          time.sleep(poll_sec)

        print(f"Fin de Home Robot {robot_name} por juntas de target: {target_name}")
        return True
      except Exception as joints_exc:
        print(
          f"ADVERTENCIA: Fallo Home {robot_name} por juntas ({target_name}): {joints_exc}"
        )

  print(f"ADVERTENCIA: No se pudo completar Home {robot_name} con ningun target disponible.")
  return False


def execute_operation_cycle(robot, robot_name, frame, pos_afuera, pos_dentro, pos_x, speed_table, time_table, op_key):
  try:
    op_speed = get_op_speed_cfg(speed_table, op_key)
    op_time_sec = get_operation_time_sec(time_table, op_key)
    robot.setPoseFrame(frame)

    move_to_afuera = "L" if FORCE_LINEAR_PROCESS_TRAJECTORY else "J"
    move_to_afuera_fallback = "J" if move_to_afuera == "L" else None

    set_speed_from_cfg(robot, op_speed["travel"])
    move_with_fallback(
      robot,
      robot_name,
      move_to_afuera,
      move_to_afuera_fallback,
      pos_afuera,
      f"{op_key}-Move{move_to_afuera}-Afuera",
    )

    set_speed_from_cfg(robot, op_speed["process"])
    move_with_timeout(robot, robot_name, "L", pos_dentro, f"{op_key}-MoveL-Dentro")
    move_with_timeout(robot, robot_name, "L", pos_x, f"{op_key}-MoveL-X")

    hold_process_time(op_time_sec, robot_name, op_key)

    set_speed_from_cfg(robot, op_speed["travel"])
    move_with_fallback(
      robot,
      robot_name,
      "L",
      "J",
      pos_afuera,
      f"{op_key}-MoveL-Salida",
    )
    return True
  except Exception as exc:
    print(f"ADVERTENCIA: Operacion {robot_name} {op_key} interrumpida: {format_exception(exc)}")
    return False


def run_timed_operation(op_name, operation_fn):
  print(f"Inicio de {op_name}")
  op_start = timer()
  ok = operation_fn()
  elapsed = timer() - op_start
  status = "OK" if ok else "WARN"
  print(f"Fin de {op_name} [{status}] | Duracion real: {elapsed:.3f} s")

# get the Targets:
#frame = RDK.Item('Frame_Pieza', ITEM_TYPE_FRAME)
#if not frame.Valid():
#    raise Exception("No encontré el frame 'Frame_Pieza'. Verifica el nombre en el árbol de RoboDK.")

#frameR1 = RDK.Item('R1_Op_00')
#if not frameR1.Valid():
#    raise Exception("No encontré el frame 'Frame_Pieza'. Verifica el nombre en el árbol de RoboDK.")


#frameBase = RDK.Item('R1_Base')
#if not frameR1.Valid():
#    raise Exception("No encontré el frame 'Frame_Pieza'. Verifica el nombre en el árbol de RoboDK.")

#Posicion HOME
#robotR1.setPoseFrame(frameBase.Pose())
RDK_R1_Home_General_Targets = get_home_targets('R1', ['R1_Home_Gral', 'R1_Home_gral'])
RDK_R2_Home_General_Targets = get_home_targets('R2', ['R2_Home_Gral', 'R2_Home_gral'])
RDK_R1_Base_Frame = get_optional_item_any(['R1_Base'], ITEM_TYPE_FRAME)
RDK_R2_Base_Frame = get_optional_item_any(['R2_Base', 'R2_BAse'], ITEM_TYPE_FRAME)

#Posiones de Robot 1 operacion 00
RDK_R1_Op_00_Frame = get_required_item('R1_Op_00', ITEM_TYPE_FRAME)
RDK_R1_Op_00_Pos_Dentro = get_required_item('R1_Op_00_Pos_Dentro')
RDK_R1_Op_00_Pos_X = get_required_item('R1_Op_00_Pos_X')
RDK_R1_Op_00_Pos_Afuera = get_required_item('R1_Op_00_Pos_Afuera')

#Posiones de Robot 1 operacion 10
RDK_R1_Op_10_Frame = get_required_item('R1_Op_10', ITEM_TYPE_FRAME)
RDK_R1_Op_10_Pos_Dentro = get_required_item('R1_Op_10_Pos_Dentro')
RDK_R1_Op_10_Pos_X = get_required_item('R1_Op_10_Pos_X')
RDK_R1_Op_10_Pos_Afuera = get_required_item('R1_Op_10_Pos_Afuera')



#Posiones de Robot 1 operacion 20
RDK_R1_Op_20_Frame = get_required_item('R1_Op_20', ITEM_TYPE_FRAME)
RDK_R1_Op_20_Pos_Dentro = get_required_item('R1_Op_20_Pos_Dentro')
RDK_R1_Op_20_Pos_X = get_required_item('R1_Op_20_Pos_X')
RDK_R1_Op_20_Pos_Afuera = get_required_item('R1_Op_20_Pos_Afuera')

#Posiones de Robot 1 operacion 30 A
RDK_R1_Op_30_A_Frame = get_required_item('R1_Op_30_A', ITEM_TYPE_FRAME)
RDK_R1_Op_30_A_Pos_Dentro = get_required_item('R1_Op_30_A_Pos_Dentro')
RDK_R1_Op_30_A_Pos_X = get_required_item('R1_Op_30_A_Pos_X')
RDK_R1_Op_30_A_Pos_Afuera = get_required_item('R1_Op_30_A_Pos_Afuera')

#Posiones de Robot 1 operacion 30 B
RDK_R1_Op_30_B_Frame = get_required_item('R1_Op_30_B', ITEM_TYPE_FRAME)
RDK_R1_Op_30_B_Pos_Dentro = get_required_item('R1_Op_30_B_Pos_Dentro')
RDK_R1_Op_30_B_Pos_X = get_required_item('R1_Op_30_B_Pos_X')
RDK_R1_Op_30_B_Pos_Afuera = get_required_item('R1_Op_30_B_Pos_Afuera')

#Posiones de Robot 1 operacion 50
RDK_R1_Op_50_Frame = get_required_item('R1_Op_50', ITEM_TYPE_FRAME)
RDK_R1_Op_50_Pos_Dentro = get_required_item('R1_Op_50_Pos_Dentro')
RDK_R1_Op_50_Pos_X = get_required_item('R1_Op_50_Pos_X')
RDK_R1_Op_50_Pos_Afuera = get_required_item('R1_Op_50_Pos_Afuera')

#Posiones de Robot 1 operacion 60
RDK_R1_Op_60_Frame = get_required_item('R1_Op_60', ITEM_TYPE_FRAME)
RDK_R1_Op_60_Pos_Dentro = get_required_item('R1_Op_60_Pos_Dentro')
RDK_R1_Op_60_Pos_X = get_required_item('R1_Op_60_Pos_X')
RDK_R1_Op_60_Pos_Afuera = get_required_item('R1_Op_60_Pos_Afuera')

#Posiones de Robot 1 operacion 70
RDK_R1_Op_70_Frame = get_required_item('R1_Op_70', ITEM_TYPE_FRAME)
RDK_R1_Op_70_Pos_Dentro = get_required_item('R1_Op_70_Pos_Dentro')
RDK_R1_Op_70_Pos_X = get_required_item('R1_Op_70_Pos_X')
RDK_R1_Op_70_Pos_Afuera = get_required_item('R1_Op_70_Pos_Afuera')

#Posiones de Robot 2 operacion 70
RDK_R2_Op_70_Frame = get_required_item('R2_Op_70', ITEM_TYPE_FRAME)
RDK_R2_Op_70_Pos_Dentro = get_required_item('R2_Op_70_Pos_Dentro')
RDK_R2_Op_70_Pos_X = get_required_item('R2_Op_70_Pos_X')
RDK_R2_Op_70_Pos_Afuera = get_required_item('R2_Op_70_Pos_Afuera')

#Posiones de Robot 2 operacion 80
RDK_R2_Op_80_Frame = get_required_item('R2_Op_80', ITEM_TYPE_FRAME)
RDK_R2_Op_80_Pos_Dentro = get_required_item('R2_Op_80_Pos_Dentro')
RDK_R2_Op_80_Pos_X = get_required_item('R2_Op_80_Pos_X')
RDK_R2_Op_80_Pos_Afuera = get_required_item('R2_Op_80_Pos_Afuera')

#Posiones de Robot 2 operacion 90
RDK_R2_Op_90_Frame = get_required_item('R2_Op_90', ITEM_TYPE_FRAME)
RDK_R2_Op_90_Pos_Dentro = get_required_item('R2_Op_90_Pos_Dentro')
RDK_R2_Op_90_Pos_X = get_required_item('R2_Op_90_Pos_X')
RDK_R2_Op_90_Pos_Afuera = get_required_item('R2_Op_90_Pos_Afuera')

#Posiones de Robot 2 operacion 100
RDK_R2_Op_100_Frame = get_required_item('R2_Op_100', ITEM_TYPE_FRAME)
RDK_R2_Op_100_Pos_Dentro = get_required_item('R2_Op_100_Pos_Dentro')
RDK_R2_Op_100_Pos_X = get_required_item('R2_Op_100_Pos_X')
RDK_R2_Op_100_Pos_Afuera = get_required_item('R2_Op_100_Pos_Afuera')

#Posiones de Robot 2 operacion 110 
RDK_R2_Op_110_Frame = get_required_item('R2_Op_110', ITEM_TYPE_FRAME)
RDK_R2_Op_110_Pos_Dentro = get_required_item('R2_Op_110_Pos_Dentro')
RDK_R2_Op_110_Pos_X = get_required_item('R2_Op_110_Pos_X')
RDK_R2_Op_110_Pos_Afuera = get_required_item('R2_Op_110_Pos_Afuera')



#Posiones de Robot 2 operacion 120
RDK_R2_Op_120_Frame = get_required_item('R2_Op_120', ITEM_TYPE_FRAME)
RDK_R2_Op_120_Pos_Dentro = get_required_item('R2_Op_120_Pos_Dentro')
RDK_R2_Op_120_Pos_X = get_required_item('R2_Op_120_Pos_X')
RDK_R2_Op_120_Pos_Afuera = get_required_item('R2_Op_120_Pos_Afuera')

#Posiones de Robot 2 operacion 130
RDK_R2_Op_130_Frame = get_required_item('R2_Op_130', ITEM_TYPE_FRAME)
RDK_R2_Op_130_Pos_Dentro = get_required_item('R2_Op_130_Pos_Dentro')
RDK_R2_Op_130_Pos_X = get_required_item('R2_Op_130_Pos_X')
RDK_R2_Op_130_Pos_Afuera = get_required_item('R2_Op_130_Pos_Afuera')

#Posiones de Robot 2 operacion 140
RDK_R2_Op_140_Frame = get_required_item('R2_Op_140', ITEM_TYPE_FRAME)
RDK_R2_Op_140_Pos_Dentro = get_required_item('R2_Op_140_Pos_Dentro')
RDK_R2_Op_140_Pos_X = get_required_item('R2_Op_140_Pos_X')
RDK_R2_Op_140_Pos_Afuera = get_required_item('R2_Op_140_Pos_Afuera')


#move posicion Home Robot 1
# robotR1.setSpeed(400,50)

move_home_with_timeout(robotR1, "R1", RDK_R1_Home_General_Targets, RDK_R1_Base_Frame)

#move posicion Home Robot 2
move_home_with_timeout(robotR2, "R2", RDK_R2_Home_General_Targets, RDK_R2_Base_Frame)



#############################Movimientos Robot 1
#robotR1.setPoseFrame(frameR1.Pose())




def R1_Op_00():
  run_timed_operation(
    "R1_Op_00",
    lambda: execute_operation_cycle(
      robotR1,
      "R1",
      RDK_R1_Op_00_Frame,
      RDK_R1_Op_00_Pos_Afuera,
      RDK_R1_Op_00_Pos_Dentro,
      RDK_R1_Op_00_Pos_X,
      R1_OPERATION_SPEEDS,
      R1_OPERATION_TIMES_SEC,
      "OP_00",
    ),
  )


def R1_Op_10():
  run_timed_operation(
    "R1_Op_10",
    lambda: execute_operation_cycle(
      robotR1,
      "R1",
      RDK_R1_Op_10_Frame,
      RDK_R1_Op_10_Pos_Afuera,
      RDK_R1_Op_10_Pos_Dentro,
      RDK_R1_Op_10_Pos_X,
      R1_OPERATION_SPEEDS,
      R1_OPERATION_TIMES_SEC,
      "OP_10",
    ),
  )




def R1_Op_20():
  run_timed_operation(
    "R1_Op_20",
    lambda: execute_operation_cycle(
      robotR1,
      "R1",
      RDK_R1_Op_20_Frame,
      RDK_R1_Op_20_Pos_Afuera,
      RDK_R1_Op_20_Pos_Dentro,
      RDK_R1_Op_20_Pos_X,
      R1_OPERATION_SPEEDS,
      R1_OPERATION_TIMES_SEC,
      "OP_20",
    ),
  )


def R1_Op_30_A():
  run_timed_operation(
    "R1_Op_30_A",
    lambda: execute_operation_cycle(
      robotR1,
      "R1",
      RDK_R1_Op_30_A_Frame,
      RDK_R1_Op_30_A_Pos_Afuera,
      RDK_R1_Op_30_A_Pos_Dentro,
      RDK_R1_Op_30_A_Pos_X,
      R1_OPERATION_SPEEDS,
      R1_OPERATION_TIMES_SEC,
      "OP_30_A",
    ),
  )


def R1_Op_30_B():
  run_timed_operation(
    "R1_Op_30_B",
    lambda: execute_operation_cycle(
      robotR1,
      "R1",
      RDK_R1_Op_30_B_Frame,
      RDK_R1_Op_30_B_Pos_Afuera,
      RDK_R1_Op_30_B_Pos_Dentro,
      RDK_R1_Op_30_B_Pos_X,
      R1_OPERATION_SPEEDS,
      R1_OPERATION_TIMES_SEC,
      "OP_30_B",
    ),
  )


def R1_Op_50():
  run_timed_operation(
    "R1_Op_50",
    lambda: execute_operation_cycle(
      robotR1,
      "R1",
      RDK_R1_Op_50_Frame,
      RDK_R1_Op_50_Pos_Afuera,
      RDK_R1_Op_50_Pos_Dentro,
      RDK_R1_Op_50_Pos_X,
      R1_OPERATION_SPEEDS,
      R1_OPERATION_TIMES_SEC,
      "OP_50",
    ),
  )



def R1_Op_60():
  run_timed_operation(
    "R1_Op_60",
    lambda: execute_operation_cycle(
      robotR1,
      "R1",
      RDK_R1_Op_60_Frame,
      RDK_R1_Op_60_Pos_Afuera,
      RDK_R1_Op_60_Pos_Dentro,
      RDK_R1_Op_60_Pos_X,
      R1_OPERATION_SPEEDS,
      R1_OPERATION_TIMES_SEC,
      "OP_60",
    ),
  )



def R1_Op_70():
  run_timed_operation(
    "R1_Op_70",
    lambda: execute_operation_cycle(
      robotR1,
      "R1",
      RDK_R1_Op_70_Frame,
      RDK_R1_Op_70_Pos_Afuera,
      RDK_R1_Op_70_Pos_Dentro,
      RDK_R1_Op_70_Pos_X,
      R1_OPERATION_SPEEDS,
      R1_OPERATION_TIMES_SEC,
      "OP_70",
    ),
  )


def R2_Op_70():
  run_timed_operation(
    "R2_Op_70",
    lambda: execute_operation_cycle(
      robotR2,
      "R2",
      RDK_R2_Op_70_Frame,
      RDK_R2_Op_70_Pos_Afuera,
      RDK_R2_Op_70_Pos_Dentro,
      RDK_R2_Op_70_Pos_X,
      R2_OPERATION_SPEEDS,
      R2_OPERATION_TIMES_SEC,
      "OP_70",
    ),
  )


def R2_Op_80():
  run_timed_operation(
    "R2_Op_80",
    lambda: execute_operation_cycle(
      robotR2,
      "R2",
      RDK_R2_Op_80_Frame,
      RDK_R2_Op_80_Pos_Afuera,
      RDK_R2_Op_80_Pos_Dentro,
      RDK_R2_Op_80_Pos_X,
      R2_OPERATION_SPEEDS,
      R2_OPERATION_TIMES_SEC,
      "OP_80",
    ),
  )


def R2_Op_90():
  run_timed_operation(
    "R2_Op_90",
    lambda: execute_operation_cycle(
      robotR2,
      "R2",
      RDK_R2_Op_90_Frame,
      RDK_R2_Op_90_Pos_Afuera,
      RDK_R2_Op_90_Pos_Dentro,
      RDK_R2_Op_90_Pos_X,
      R2_OPERATION_SPEEDS,
      R2_OPERATION_TIMES_SEC,
      "OP_90",
    ),
  )


def R2_Op_100():
  run_timed_operation(
    "R2_Op_100",
    lambda: execute_operation_cycle(
      robotR2,
      "R2",
      RDK_R2_Op_100_Frame,
      RDK_R2_Op_100_Pos_Afuera,
      RDK_R2_Op_100_Pos_Dentro,
      RDK_R2_Op_100_Pos_X,
      R2_OPERATION_SPEEDS,
      R2_OPERATION_TIMES_SEC,
      "OP_100",
    ),
  )


def R2_Op_110():
  run_timed_operation(
    "R2_Op_110",
    lambda: execute_operation_cycle(
      robotR2,
      "R2",
      RDK_R2_Op_110_Frame,
      RDK_R2_Op_110_Pos_Afuera,
      RDK_R2_Op_110_Pos_Dentro,
      RDK_R2_Op_110_Pos_X,
      R2_OPERATION_SPEEDS,
      R2_OPERATION_TIMES_SEC,
      "OP_110",
    ),
  )



def R2_Op_120():
  run_timed_operation(
    "R2_Op_120",
    lambda: execute_operation_cycle(
      robotR2,
      "R2",
      RDK_R2_Op_120_Frame,
      RDK_R2_Op_120_Pos_Afuera,
      RDK_R2_Op_120_Pos_Dentro,
      RDK_R2_Op_120_Pos_X,
      R2_OPERATION_SPEEDS,
      R2_OPERATION_TIMES_SEC,
      "OP_120",
    ),
  )


def R2_Op_130():
  run_timed_operation(
    "R2_Op_130",
    lambda: execute_operation_cycle(
      robotR2,
      "R2",
      RDK_R2_Op_130_Frame,
      RDK_R2_Op_130_Pos_Afuera,
      RDK_R2_Op_130_Pos_Dentro,
      RDK_R2_Op_130_Pos_X,
      R2_OPERATION_SPEEDS,
      R2_OPERATION_TIMES_SEC,
      "OP_130",
    ),
  )


def R2_Op_140():
  run_timed_operation(
    "R2_Op_140",
    lambda: execute_operation_cycle(
      robotR2,
      "R2",
      RDK_R2_Op_140_Frame,
      RDK_R2_Op_140_Pos_Afuera,
      RDK_R2_Op_140_Pos_Dentro,
      RDK_R2_Op_140_Pos_X,
      R2_OPERATION_SPEEDS,
      R2_OPERATION_TIMES_SEC,
      "OP_140",
    ),
  )


# Crea funciones de Pick and Place para cada operación, por ejemplo:
# Pick OP 00 and place in OP 10

def R1_pick_and_place_op_00_to_10():
  R1_Op_00()
  R1_Op_10()





def R1_pick_and_place_op_10_to_20():
  R1_Op_10()
  R1_Op_20()

def R1_pick_and_place_op_20_to_30_A():
  R1_Op_20()
  R1_Op_30_A()

def R1_pick_and_place_op_20_to_30_B():
  R1_Op_20()
  R1_Op_30_B()

def R1_pick_and_place_op_30_A_to_60():
  R1_Op_30_A()
  R1_Op_60()

def R1_pick_and_place_op_30_B_to_60():
  R1_Op_30_B()
  R1_Op_60()

def R1_pick_and_place_op_60_to_70():
  R1_Op_60()
  R1_Op_70()


def R2_pick_and_place_op_70_to_80():
  R2_Op_70()
  R2_Op_80()

def R2_pick_and_place_op_80_to_90():
  R2_Op_80()
  R2_Op_90()

def R2_pick_and_place_op_90_to_100():
  R2_Op_90()
  R2_Op_100()

def R2_pick_and_place_op_100_to_110():
  R2_Op_100()
  R2_Op_110()


def R2_pick_and_place_op_110_to_120():
  R2_Op_110()
  R2_Op_120()

def R2_pick_and_place_op_120_to_130():
  R2_Op_120()
  R2_Op_130()

def R2_pick_and_place_op_130_to_140():
  R2_Op_130()
  R2_Op_140()




print("Ejecutando pick and place OP 00 to OP 10")
R1_pick_and_place_op_00_to_10()



print("Ejecutando pick and place OP 10 B to OP 20")
R1_pick_and_place_op_10_to_20()  

print("Ejecutando pick and place OP 20 to OP 30 A")
R1_pick_and_place_op_20_to_30_A()
print("Ejecutando pick and place OP 30 A to OP 60")
R1_pick_and_place_op_30_A_to_60()

#print("Ejecutando pick and place OP 30 B to OP 60")
#R1_pick_and_place_op_30_B_to_60()
print("Ejecutando pick  and place OP 60 to OP 70")
R1_pick_and_place_op_60_to_70() 

print("Ejecutando pick and place OP 70 to OP 80")
R2_pick_and_place_op_70_to_80() 


print("Ejecutando pick and place OP 80 to OP 90")
R2_pick_and_place_op_80_to_90()


#print("Ejecutando pick and place OP 90 to OP 100")
#R2_pick_and_place_op_90_to_100()  


print("Ejecutando pick and place OP 100 to OP 110")
R2_pick_and_place_op_100_to_110()
print("Ejecutando pick and place OP 110 to OP 120")
R2_pick_and_place_op_110_to_120() 
print("Ejecutando pick and place OP 120 to OP 130")
R2_pick_and_place_op_120_to_130()
print("Ejecutando pick and place OP 130 to OP 140")
R2_pick_and_place_op_130_to_140()


#move posicion Home Robot 1
# robotR1.setSpeed(400,50)

move_home_with_timeout(robotR1, "R1", RDK_R1_Home_General_Targets, RDK_R1_Base_Frame)

#move posicion Home Robot 2
move_home_with_timeout(robotR2, "R2", RDK_R2_Home_General_Targets, RDK_R2_Base_Frame)



end_time=timer()
print(f"Tiempo de ejecucion: {end_time - start_time:.6f}segundos")