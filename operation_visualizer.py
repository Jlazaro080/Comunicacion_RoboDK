"""
Operation Timing Visualizer & Metrics
Genera gráficos de tiempo y análisis de operaciones
"""

import time
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OperationExecution:
    """Registro de ejecución de una operación"""
    op_name: str
    robot: str
    start_time: float
    end_time: float
    parts_processed: int
    success: bool
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class OperationMetrics:
    """Recolector y analizador de métricas de operaciones"""
    
    def __init__(self):
        self.executions: List[OperationExecution] = []
        self.cycle_start_time: float = None
        self.cycle_count: int = 0
    
    def start_cycle(self) -> None:
        """Marca inicio de ciclo"""
        self.cycle_start_time = time.time()
    
    def record_execution(self, op_name: str, robot: str, 
                        parts_processed: int = 1, success: bool = True) -> OperationExecution:
        """Registra ejecución de operación"""
        execution = OperationExecution(
            op_name=op_name,
            robot=robot,
            start_time=time.time(),
            end_time=time.time(),
            parts_processed=parts_processed,
            success=success
        )
        self.executions.append(execution)
        return execution
    
    def get_summary(self) -> Dict:
        """Retorna resumen de métricas"""
        if not self.executions:
            return {"error": "Sin ejecuciones registradas"}
        
        total_time = sum(e.duration for e in self.executions)
        successful = sum(1 for e in self.executions if e.success)
        total_parts = sum(e.parts_processed for e in self.executions)
        
        # Tiempo por operación
        op_times = {}
        for e in self.executions:
            if e.op_name not in op_times:
                op_times[e.op_name] = {"count": 0, "total": 0}
            op_times[e.op_name]["count"] += 1
            op_times[e.op_name]["total"] += e.duration
        
        # Tiempo por robot
        robot_times = {}
        for e in self.executions:
            if e.robot not in robot_times:
                robot_times[e.robot] = {"count": 0, "total": 0}
            robot_times[e.robot]["count"] += 1
            robot_times[e.robot]["total"] += e.duration
        
        return {
            "total_executions": len(self.executions),
            "successful_executions": successful,
            "total_time_s": total_time,
            "total_parts_processed": total_parts,
            "average_execution_time_s": total_time / len(self.executions),
            "operation_times": op_times,
            "robot_times": robot_times
        }
    
    def print_report(self) -> None:
        """Imprime reporte de métricas"""
        summary = self.get_summary()
        
        if "error" in summary:
            print(f"[WARN] {summary['error']}")
            return
        
        print("\n" + "="*80)
        print("REPORTE DE MÉTRICAS DE OPERACIONES")
        print("="*80)
        
        print(f"\n[RESUMEN GENERAL]")
        print(f"  - Total ejecuciones: {summary['total_executions']}")
        print(f"  - Ejecuciones exitosas: {summary['successful_executions']}")
        print(f"  - Tiempo total: {summary['total_time_s']:.2f}s")
        print(f"  - Piezas procesadas: {summary['total_parts_processed']}")
        print(f"  - Tiempo promedio/ejecucion: {summary['average_execution_time_s']:.3f}s")
        
        print(f"\n[TIEMPOS POR OPERACION]")
        for op_name, times in sorted(summary['operation_times'].items()):
            avg = times['total'] / times['count']
            print(f"  - {op_name}:")
            print(f"    - Ejecuciones: {times['count']}")
            print(f"    - Tiempo total: {times['total']:.2f}s")
            print(f"    - Tiempo promedio: {avg:.3f}s")
        
        print(f"\n[TIEMPOS POR ROBOT]")
        for robot, times in sorted(summary['robot_times'].items()):
            avg = times['total'] / times['count']
            utilization = (times['total'] / summary['total_time_s'] * 100) if summary['total_time_s'] > 0 else 0
            print(f"  - {robot}:")
            print(f"    - Ejecuciones: {times['count']}")
            print(f"    - Tiempo total: {times['total']:.2f}s")
            print(f"    - Tiempo promedio: {avg:.3f}s")
            print(f"    - Utilizacion: {utilization:.1f}%")
        
        print("\n")
    
    def timeline_ascii(self, max_width: int = 80) -> None:
        """Genera timeline ASCII de ejecuciones"""
        if not self.executions:
            print("[WARN] Sin ejecuciones para mostrar timeline")
            return
        
        print("\n" + "="*80)
        print("TIMELINE DE EJECUCIONES")
        print("="*80 + "\n")
        
        # Agrupar por robot
        robots = {}
        for e in self.executions:
            if e.robot not in robots:
                robots[e.robot] = []
            robots[e.robot].append(e)
        
        # Mostrar timeline para cada robot
        for robot in sorted(robots.keys()):
            print(f"{robot}:")
            
            for e in robots[robot]:
                # Barra con duración
                bar_length = int(e.duration * 10)  # Escala 1s = 10 caracteres
                bar = "#" * max(1, bar_length)
                status = "OK" if e.success else "ERR"
                print(f"  {status} {e.op_name:15} |{bar:30}| {e.duration:.2f}s ({e.parts_processed} piezas)")
            
            print()


class GraphicalReport:
    """Genera reportes gráficos en texto plano"""
    
    @staticmethod
    def bar_chart(data: Dict[str, float], title: str = "", max_width: int = 40) -> None:
        """Crea gráfico de barras en ASCII"""
        if not data:
            print(f"[WARN] {title}: Sin datos")
            return
        
        print(f"\n{title}")
        print("-" * (len(title)))
        
        max_value = max(data.values()) if data.values() else 1
        
        for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
            bar_length = int((value / max_value) * max_width)
            bar = "#" * bar_length + "." * (max_width - bar_length)
            print(f"  {label:20} |{bar}| {value:8.2f}")
    
    @staticmethod
    def distribution_pie(data: Dict[str, float], title: str = "") -> None:
        """Muestra distribución simple"""
        if not data:
            return
        
        print(f"\n{title}")
        print("-" * (len(title)))
        
        total = sum(data.values())
        for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
            percentage = (value / total * 100) if total > 0 else 0
            bar_length = int(percentage / 2)  # 50 caracteres = 100%
            bar = "#" * bar_length
            print(f"  {label:20} {bar:25} {percentage:5.1f}%")


if __name__ == "__main__":
    # Ejemplo de uso
    metrics = OperationMetrics()
    
    # Simular algunas ejecuciones
    metrics.record_execution("Op_10", "R1", 5, True)
    metrics.executions[-1].end_time = time.time() + 1.5
    
    metrics.record_execution("Op_20", "R1", 1, True)
    metrics.executions[-1].end_time = time.time() + 2.5
    
    metrics.record_execution("Op_70", "R1", 2, True)
    metrics.executions[-1].end_time = time.time() + 1.5
    
    metrics.record_execution("Op_70", "R2", 1, True)
    metrics.executions[-1].end_time = time.time() + 2.0
    
    # Mostrar reportes
    metrics.print_report()
    metrics.timeline_ascii()
    
    # Gráficos
    summary = metrics.get_summary()
    op_times = {op: info['total'] for op, info in summary['operation_times'].items()}
    GraphicalReport.bar_chart(op_times, "Tiempo total por operación (segundos)")
    
    robot_times = {robot: info['total'] for robot, info in summary['robot_times'].items()}
    GraphicalReport.distribution_pie(robot_times, "Distribución de tiempo por robot")
