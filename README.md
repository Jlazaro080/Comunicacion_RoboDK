# Sistema de Programación Dinámica de Operaciones RoboDK

## 📋 Descripción General

Sistema completo para reemplazar la secuencia fija de operaciones en RoboDK por un **control dinámico basado en disponibilidad de máquinas**. Incluye:

- ✅ **Scheduler dinámico**: Selecciona operaciones según prioridad y disponibilidad
- ✅ **Tracking de piezas**: Sigue cada pieza a través de las operaciones
- ✅ **Configuración por CSV**: Define operaciones sin cambiar código
- ✅ **Tiempos ajustables**: Modifica tiempo de procesamiento en tiempo de ejecución
- ✅ **Métricas y análisis**: Gráficos de tiempos y utilización de robots
- ✅ **Integración con RoboDK**: Uso directo con robolink

---

## 🗂️ Estructura de Archivos

```
Comunicacion_RoboDK/
├── Comunicacion_RoboDk_V01.py          # Script principal original de RoboDK
├── OperationScheduler.py               # 🆕 Motor de scheduler dinámico
├── csv_loader.py                       # 🆕 Cargador de configuraciones CSV
├── operation_visualizer.py             # 🆕 Métricas y gráficos ASCII
├── integration_example.py              # 🆕 Ejemplo de integración con RoboDK
├── operations_config.csv               # 🆕 Configuración de operaciones
├── tiempos_robodk.csv                  # CSV original de tiempos
└── README.md                           # Este archivo
```

---

## 🚀 Uso Rápido

### 1️⃣ **Opción A: Ejecutar Scheduler Usando CSV**

```bash
python OperationScheduler.py
```

**Qué hace:**
- Lee `operations_config.csv`
- Crea automáticamente operaciones (Op_10, Op_20, Op_70, etc.)
- Ejecuta 2 ciclos de forma dinámica
- Muestra métricas y gráficos ASCII

---

### 2️⃣ **Opción B: Cargar y Analizar Configuraciones**

```bash
python csv_loader.py
```

**Output:**
- Sumario de todas las operaciones configuradas
- Prioridad, tiempos, piezas de entrada/salida
- Velocidades de ejecución

---

### 3️⃣ **Opción C: Ejemplo de Integración con RoboDK**

```bash
python integration_example.py
```

**Qué hace:**
- Conecta con RoboDK (si está activo)
- Carga robots R1 y R2
- Ejecuta operaciones dinámicamente
- Muestra cómo integrar en tu código existente

---

## 📝 Formato CSV - `operations_config.csv`

```csv
operation_name,robot,priority,work_time_s,input_parts,output_parts,passes,requires_r2_free,frames,speeds_linear_mm_s,speeds_joint_deg_s
Op_10,R1,2,1.5,1,1,2,False,"R1_Op_10|R1_Op_10_Pos_Afuera|R1_Op_10_Pos_Dentro",500,350
Op_20,R1,3,2.5,1,1,1,False,"R1_Op_20|R1_Op_20_Pos_Afuera|R1_Op_20_Pos_Dentro",500,350
Op_70,R1,5,1.5,1,2,1,False,"R1_Op_70|R1_Op_70_Pos_Afuera|R1_Op_70_Pos_Dentro",500,350
Op_70,R2,5,2.0,1,1,1,False,"R2_Op_70|R2_Op_70_Pos_Afuera|R2_Op_70_Pos_Dentro",500,350
```

### Campos:
| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `operation_name` | Nombre único | Op_10, Op_20 |
| `robot` | Robot asignado | R1, R2 |
| `priority` | Mayor = ejecuta primero | 1-10 |
| `work_time_s` | Tiempo de procesamiento | 1.5 |
| `input_parts` | Piezas requeridas entrada | 1, 2 |
| `output_parts` | Piezas generadas salida | 1, 2 |
| `passes` | Repeticiones por ciclo | 1, 2, 3 |
| `requires_r2_free` | Espera a R2 disponible | True, False |
| `frames` | Targets RoboDK (sep. `\|`) | R1_Op_10\|Pos_Afuera\|Pos_Dentro |
| `speeds_linear_mm_s` | Velocidad lineal | 500 |
| `speeds_joint_deg_s` | Velocidad rotacional | 350 |

---

## 🔧 API - Clases Principales

### 1. **OperationScheduler.py**

#### `Operation` (dataclass)
```python
op = Operation(
    name='Op_10',
    robot='R1',
    frames={'frame': 'R1_Op_10', 'targets': ['Pos_Afuera', 'Pos_Dentro']},
    speeds={'linear_mm_s': 500, 'joint_deg_s': 350},
    work_time_s=1.5,     # ⭐ Configurable
    priority=2,
    passes=2,
    input_parts_needed=1,
    output_parts_generated=1
)
```

#### `DynamicCycleController` (orquestador)
```python
controller = DynamicCycleController(num_r1=1, num_r2=1, total_cycles=5)

# Añadir operación
controller.add_operation_to_queue(op)

# Ajustar tiempo (dinámico, sin reiniciar)
controller.set_operation_work_time('Op_10', 2.0)  # Cambia a 2 segundos

# Ejecutar
controller.run_all_cycles(callback_execute=my_function)
```

#### Callback de ejecución
```python
def execute_op(operation: Operation):
    """Callback llamado por el scheduler"""
    print(f"Ejecutando {operation.name} en {operation.robot}")
    # Aquí: robot.MoveJ(), robot.MoveL(), etc.
    time.sleep(operation.work_time_s)

controller.run_all_cycles(callback_execute=execute_op)
```

---

### 2. **csv_loader.py**

```python
from csv_loader import OperationConfigLoader

loader = OperationConfigLoader()
configs = loader.load_from_csv('operations_config.csv')  # Dict[str, OperationConfig]

loader.print_summary(configs)  # Muestra tabla de operaciones
```

---

### 3. **operation_visualizer.py**

```python
from operation_visualizer import OperationMetrics, GraphicalReport

metrics = OperationMetrics()
metrics.start_cycle()

# Después de ejecutar operaciones...
metrics.record_execution('Op_10', 'R1', parts_processed=5, success=True)
metrics.record_execution('Op_20', 'R1', parts_processed=1, success=True)

# Mostrar reportes
metrics.print_report()
metrics.timeline_ascii()

# Gráficos
summary = metrics.get_summary()
op_times = {op: info['total'] for op, info in summary['operation_times'].items()}
GraphicalReport.bar_chart(op_times, "Tiempo por operación")
GraphicalReport.distribution_pie(op_times, "Distribución")
```

---

## 💡 Ejemplos de Código

### Ejemplo 1: Crear scheduler desde código (sin CSV)

```python
from OperationScheduler import DynamicCycleController, Operation

# Crear controller
controller = DynamicCycleController(num_r1=1, num_r2=1, total_cycles=3)

# Crear operación
op = Operation(
    name='Op_10',
    robot='R1',
    frames={'primary': 'R1_Op_10'},
    speeds={'linear_mm_s': 500},
    work_time_s=1.5,
    priority=2,
    passes=2
)

# Añadir y ejecutar
controller.add_operation_to_queue(op)
controller.run_all_cycles(callback_execute=lambda o: print(f"Ejecutando {o.name}"))
```

---

### Ejemplo 2: Cargar desde CSV y ajustar dinámicamente

```python
from OperationScheduler import DynamicCycleController
from csv_loader import OperationConfigLoader

controller = DynamicCycleController(num_r1=1, num_r2=1, total_cycles=5)

# Cargar desde CSV
loader = OperationConfigLoader()
configs = loader.load_from_csv('operations_config.csv')

for config in configs.values():
    op = Operation(
        name=config.operation_name,
        robot=config.robot,
        frames={'primary': config.frames[0]},
        speeds={'linear_mm_s': config.speeds_linear_mm_s},
        work_time_s=config.work_time_s,
        priority=config.priority,
        passes=config.passes
    )
    controller.add_operation_to_queue(op)

# AJUSTE DINÁMICO: Cambiar tiempos antes de ejecutar
controller.set_operation_work_time('Op_10', 2.0)  # Op_10 ahora toma 2s
controller.set_operation_work_time('Op_20', 3.5)  # Op_20 ahora toma 3.5s

# Ejecutar
controller.run_all_cycles(callback_execute=lambda o: time.sleep(o.work_time_s))
```

---

### Ejemplo 3: Tracking de piezas

```python
from OperationScheduler import DynamicCycleController, Operation, PartBuffer

controller = DynamicCycleController(num_r1=1, num_r2=1, total_cycles=2)

# Crear operaciones
op_10 = Operation(name='Op_10', robot='R1', frames={}, speeds={},
                  work_time_s=1.5, input_parts_needed=1, output_parts_generated=2)
op_70 = Operation(name='Op_70', robot='R1', frames={}, speeds={},
                  work_time_s=2.0, input_parts_needed=2, output_parts_generated=1)

controller.add_operation_to_queue(op_10)
controller.add_operation_to_queue(op_70)

# Conectar buffers: Salida de Op_10 → Entrada de Op_70
salida_op10 = controller.queue.operations['Op_10_R1'].output_buffer
entrada_op70 = controller.queue.operations['Op_70_R1'].input_buffer
entrada_op70 = salida_op10  # Conexión directa

# Añadir piezas iniciales
salida_op10.add_parts(5)

# Ejecutar - Op_10 genera piezas, Op_70 las consume
controller.run_all_cycles(callback_execute=lambda o: print(f"Ejecutando {o.name}"))
```

---

## 🎯 Ventajas vs. Secuencia Fija

| Aspecto | Secuencia Fija | Scheduler Dinámico |
|--------|-----------|------------------|
| **Control** | Fijo, inmutable | Flexible, basado en disponibilidad |
| **Adaptación** | Requiere código | Ajustes sin código (CSV) |
| **Tiempos** | Hardcodeados | Configurables (+modificables en runtime) |
| **Piezas** | No hay tracking | Buffer con seguimiento completo |
| **Paralelismo** | Manual | Automático (R1/R2) |
| **Análisis** | Manual | Métricas+gráficos automáticas |
| **Escalabilidad** | Difícil | Fácil (añadir robots/operaciones) |

---

## 🔗 Integración con `Comunicacion_RoboDk_V01.py`

### Paso 1: Reemplazar el loop principal

```python
# ORIGINAL (fijo):
while True:
    # ejecutar Op_00, Op_10, Op_20, ...
    for op in FIXED_SEQUENCE:
        execute_robot_step(robot, op, ...)

# NUEVO (dinámico):
from OperationScheduler import DynamicCycleController
from csv_loader import OperationConfigLoader

controller = DynamicCycleController(num_r1=1, num_r2=1, total_cycles=3)
loader = OperationConfigLoader()

# Cargar desde CSV
for config in loader.load_from_csv('operations_config.csv').values():
    op = Operation(...)  # Crear desde config
    controller.add_operation_to_queue(op)

# Ejecutar dinámicamente
controller.run_all_cycles(callback_execute=execute_robot_step)
```

### Paso 2: Adaptar callback

```python
def execute_robot_step_dynamic(operation: Operation):
    """Callback que integra con la lógica existente de RoboDK"""
    
    robot = RDK.Item(operation.robot, ITEM_TYPE_ROBOT)
    frame = RDK.Item(operation.frames['primary'])
    
    robot.setPoseFrame(frame)
    
    # Aplicar velocidad
    robot.setSpeed(operation.speeds.get('linear_mm_s', 500))
    
    # Ejecutar targets en secuencia
    for target_name in operation.frames.get('targets', []):
        target = RDK.Item(target_name)
        robot.MoveL(target)  # o MoveJ según corresponda
    
    robot.WaitMove()
    time.sleep(operation.work_time_s)

controller.run_all_cycles(callback_execute=execute_robot_step_dynamic)
```

---

## 📊 Interpretación de Métricas

```
📊 RESUMEN GENERAL:
  ├─ Total ejecuciones: 8
  ├─ Ejecuciones exitosas: 8
  ├─ Tiempo total: 14.35s
  ├─ Piezas procesadas: 12
  └─ Tiempo promedio/ejecución: 1.794s

⏱️  TIEMPOS POR OPERACIÓN:
  ├─ Op_10:
  │  ├─ Ejecuciones: 2
  │  ├─ Tiempo total: 3.00s
  │  └─ Tiempo promedio: 1.500s

🤖 TIEMPOS POR ROBOT:
  ├─ R1:
  │  ├─ Ejecuciones: 5
  │  ├─ Tiempo total: 8.45s
  │  └─ Utilización: 58.9%
```

- **Utilización baja**: Robot ocioso (aumentar piezas de entrada)
- **Utilización alta**: Robot saturado (optimizar tiempos)
- **Desequilibrio R1 vs R2**: Reajustar prioridades o cargas

---

## ⚙️ Configuración Avanzada

### Ajustar Prioridades

En `operations_config.csv`, aumentar `priority`:
```csv
Op_20,R1,10,2.5,1,1,1,False,...  # Ahora prioridad 10 (máxima)
Op_10,R1,2,1.5,1,1,2,False,...   # Baja a 2
```

### Añadir Restricciones

```python
op = Operation(
    ...,
    requires_r2_free=True  # Op espera a que R2 esté libre
)
```

### Modificar Tiempos en Tiempo Real

```python
# Antes de ejecutar
controller.set_operation_work_time('Op_10', 0.5)  # Más rápido
controller.set_operation_work_time('Op_20', 5.0)  # Más lento
```

---

## 🐛 Troubleshooting

### Error: "csv_loader not found"
→ Asegurar `csv_loader.py` está en el mismo directorio

### Error: "operations_config.csv not found"
→ Crear archivo CSV en el directorio actual o especificar ruta completa

### Robot no se mueve en RoboDK
→ Revisar `frames` en CSV coinciden con nombres exactos en RoboDK

### Métricas vacías
→ Asegurar `operation_visualizer.py` está disponible e instalado

### Piezas no fluyen entre operaciones
→ Verificar conexión de buffers en el código

---

## 📚 Próximos Pasos

1. **Implementar callbacks reales de RoboDK** en `integration_example.py`
2. **Crear dashboard Tkinter** con visualización en tiempo real
3. **Añadir persistencia** (guardar/cargar estados)
4. **Implementar recuperación de errores** (reintentos automáticos)
5. **Expandir tracking** (trazabilidad completa de piezas)

---

## 📞 Soporte

Para preguntas o problemas:
1. Revisar logs de ejecución
2. Ejecutar `python csv_loader.py` para validar CSV
3. Ejecutar `python operation_visualizer.py` para probar métricas
4. Revisar `integration_example.py` para ejemplos de integración

---

**Versión**: 2.0 | **Último update**: Marzo 2026
