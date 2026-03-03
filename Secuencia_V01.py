# Type help("robodk.robolink") or help("robodk.robomath") for more information
# Press F5 to run the script
# Documentation: https://robodk.com/doc/en/RoboDK-API.html
# Reference:     https://robodk.com/doc/en/PythonAPI/robodk.html
# Note: It is not required to keep a copy of this file, your Python script is saved with your RDK project

# You can also use the new version of the API:
from robodk import robolink    # RoboDK API
from robodk import robomath    # Robot toolbox
RDK = robolink.Robolink()

# Forward and backwards compatible use of the RoboDK API:
# Remove these 2 lines to follow python programming guidelines
from robodk import *      # RoboDK API
from robolink import *    # Robot toolbox
import time
import sys


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


def execute_operation_cycle(robot, robot_name, frame, pos_afuera, pos_dentro, pos_x, speed_table, time_table, op_key):
  op_speed = get_op_speed_cfg(speed_table, op_key)
  op_time_sec = get_operation_time_sec(time_table, op_key)
  robot.setPoseFrame(frame)

  set_speed_from_cfg(robot, op_speed["travel"])
  robot.MoveJ(pos_afuera)
  robot.WaitMove()

  set_speed_from_cfg(robot, op_speed["process"])
  robot.MoveL(pos_dentro)
  robot.WaitMove()
  robot.MoveL(pos_x)
  robot.WaitMove()

  hold_process_time(op_time_sec, robot_name, op_key)

  set_speed_from_cfg(robot, op_speed["travel"])
  robot.MoveL(pos_afuera)
  robot.WaitMove()


def run_timed_operation(op_name, operation_fn):
  print(f"Inicio de {op_name}")
  op_start = timer()
  operation_fn()
  elapsed = timer() - op_start
  print(f"Fin de {op_name} | Duracion real: {elapsed:.3f} s")

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
RDK_R1_Home_General = get_required_item_any(['R1_Home_Gral', 'R1_Home_gral'])
RDK_R2_Home_General = get_required_item_any(['R2_Home_Gral', 'R2_Home_gral'])

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

print("Inicio Home General R1")
robotR1.MoveJ(RDK_R1_Home_General)
robotR1.WaitMove()
print("Fin de Home Robot 1")

#move posicion Home Robot 2
print("Inicio Home General R2")
robotR2.MoveJ(RDK_R2_Home_General)
robotR2.WaitMove()
print("Fin de Home Robot 2")



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

def R1_pick_and_place_op_10_to_10():
  R1_Op_10()
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
print("Ejecutando pick and place OP 10 to OP 20")
R1_pick_and_place_op_10_to_20()  
print("Ejecutando pick and place OP 20 to OP 30 A")
R1_pick_and_place_op_20_to_30_A()
#print("Ejecutando pick and place OP 20 to OP 30 B")
#R1_pick_and_place_op_20_to_30_B()
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
print("Ejecutando pick and place OP 90 to OP 100")
R2_pick_and_place_op_90_to_100()  
print("Ejecutando pick and place OP 100 to OP 110")
R2_pick_and_place_op_100_to_110() 
print("Ejecutando pick and place OP 110 to OP 120")
R2_pick_and_place_op_110_to_120() 
print("Ejecutando pick and place OP 120 to OP 130")
R2_pick_and_place_op_120_to_130()
print("Ejecutando pick and place OP 130 to OP 140")
R2_pick_and_place_op_130_to_140()






end_time=timer()
print(f"Tiempo de ejecucion: {end_time - start_time:.6f}segundos")