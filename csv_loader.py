"""
CSV Configuration Loader for Operations
Carga configuración de operaciones desde archivo CSV
"""

import csv
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class OperationConfig:
    """Configuración de operación desde CSV"""
    operation_name: str
    robot: str
    priority: int
    work_time_s: float
    input_parts: int
    output_parts: int
    passes: int
    requires_r2_free: bool
    frames: List[str]
    speeds_linear_mm_s: int
    speeds_joint_deg_s: int


class OperationConfigLoader:
    """Cargador de configuraciones de CSV"""
    
    @staticmethod
    def load_from_csv(csv_file: str) -> Dict[str, OperationConfig]:
        """
        Carga configuración de operaciones desde CSV
        
        Args:
            csv_file: Ruta al archivo CSV
            
        Returns:
            Dict de {operation_name: OperationConfig}
        """
        configs = {}
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    if not row['operation_name'].strip():
                        continue
                    
                    # Parsear frames (separados por |)
                    frames = [f.strip() for f in row['frames'].split('|')]
                    
                    # Parsear requires_r2_free (True/False string)
                    requires_r2 = row['requires_r2_free'].strip().lower() == 'true'
                    
                    config = OperationConfig(
                        operation_name=row['operation_name'].strip(),
                        robot=row['robot'].strip(),
                        priority=int(row['priority']),
                        work_time_s=float(row['work_time_s']),
                        input_parts=int(row['input_parts']),
                        output_parts=int(row['output_parts']),
                        passes=int(row['passes']),
                        requires_r2_free=requires_r2,
                        frames=frames,
                        speeds_linear_mm_s=int(row['speeds_linear_mm_s']),
                        speeds_joint_deg_s=int(row['speeds_joint_deg_s'])
                    )
                    
                    # Usar nombre único: operation_name_robot si hay duplicados
                    unique_key = f"{config.operation_name}_{config.robot}"
                    configs[unique_key] = config
                    
        except FileNotFoundError:
            print(f"❌ ERROR: Archivo CSV no encontrado: {csv_file}")
            return {}
        except Exception as e:
            print(f"❌ ERROR al cargar CSV: {e}")
            return {}
        
        return configs
    
    @staticmethod
    def print_summary(configs: Dict[str, OperationConfig]) -> None:
        """Imprime resumen de configuraciones cargadas"""
        print("\n" + "="*80)
        print("CONFIGURACIONES DE OPERACIONES CARGADAS")
        print("="*80)
        
        for op_key, config in sorted(configs.items()):
            print(f"\n{op_key}:")
            print(f"  ├─ Robot: {config.robot}")
            print(f"  ├─ Prioridad: {config.priority}")
            print(f"  ├─ Tiempo trabajo: {config.work_time_s}s")
            print(f"  ├─ Piezas entrada/salida: {config.input_parts}/{config.output_parts}")
            print(f"  ├─ Pasadas: {config.passes}")
            print(f"  ├─ Requiere R2 libre: {config.requires_r2_free}")
            print(f"  ├─ Frames: {', '.join(config.frames[:3])}...")
            print(f"  └─ Velocidades: {config.speeds_linear_mm_s}mm/s (lineal), {config.speeds_joint_deg_s}°/s (joints)")


if __name__ == "__main__":
    # Prueba de carga
    loader = OperationConfigLoader()
    configs = loader.load_from_csv("operations_config.csv")
    loader.print_summary(configs)
