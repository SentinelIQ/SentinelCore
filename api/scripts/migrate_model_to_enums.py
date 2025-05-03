#!/usr/bin/env python
"""
Script para migrar models existentes para usar os novos enums.
Este script demonstra como refatorar uma definição de model que usa
choices inline para usar os novos enums padronizados.

Uso:
    python api/scripts/migrate_model_to_enums.py <app_name> <model_name>

Exemplo:
    python api/scripts/migrate_model_to_enums.py alerts Alert
"""
import os
import sys
import re
import django
from pathlib import Path

# Configurar ambiente Django
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentineliq.settings')
django.setup()


def print_model_choices(app_name, model_name):
    """
    Imprime os choices encontrados em um modelo e sugere substituições usando enums.
    
    Args:
        app_name (str): Nome da aplicação
        model_name (str): Nome do modelo
    """
    try:
        model_file = f"{app_name}/models.py"
        
        if not os.path.exists(model_file):
            sub_models_dir = f"{app_name}/models"
            if os.path.exists(sub_models_dir):
                model_files = [f for f in os.listdir(sub_models_dir) if f.endswith('.py')]
                for mf in model_files:
                    if model_name.lower() in mf.lower():
                        model_file = f"{sub_models_dir}/{mf}"
                        break
        
        if not os.path.exists(model_file):
            print(f"❌ Arquivo de modelo não encontrado: {model_file}")
            return
        
        print(f"📂 Analisando arquivo: {model_file}")
        
        # Ler conteúdo do arquivo
        with open(model_file, 'r') as f:
            content = f.read()
        
        # Procurar pelo modelo específico
        model_pattern = rf"class\s+{model_name}\s*\([^)]+\):"
        model_match = re.search(model_pattern, content)
        
        if not model_match:
            print(f"❌ Modelo '{model_name}' não encontrado no arquivo.")
            return
        
        model_start = model_match.start()
        
        # Encontrar o próximo modelo ou o final do arquivo
        next_model = re.search(r"class\s+\w+\s*\([^)]+\):", content[model_start + 1:])
        if next_model:
            model_end = model_start + 1 + next_model.start()
        else:
            model_end = len(content)
        
        model_content = content[model_start:model_end]
        
        # Localizar definições de choices
        choices_pattern = r"(\w+)\s*=\s*models\.\w+Field\([^)]*choices\s*=\s*([^,)]+)"
        choices_matches = re.finditer(choices_pattern, model_content)
        
        found_choices = False
        
        for match in choices_matches:
            found_choices = True
            field_name = match.group(1)
            choices_def = match.group(2)
            
            print(f"\n🔍 Encontrado campo com choices: {field_name}")
            print(f"   Definição atual: {choices_def.strip()}")
            
            # Determinar qual enum deve ser usado
            suggested_enum = None
            
            if field_name.lower() == 'status':
                if app_name == 'alerts':
                    suggested_enum = 'AlertStatusEnum'
                elif app_name == 'incidents':
                    suggested_enum = 'IncidentStatusEnum'
                elif app_name == 'tasks':
                    suggested_enum = 'TaskStatusEnum'
                else:
                    suggested_enum = 'StatusEnum'
            
            elif field_name.lower() == 'severity':
                if app_name == 'alerts':
                    suggested_enum = 'AlertSeverityEnum'
                elif app_name == 'incidents':
                    suggested_enum = 'IncidentSeverityEnum'
                else:
                    suggested_enum = 'SeverityEnum'
            
            elif field_name.lower() == 'priority':
                if app_name == 'tasks':
                    suggested_enum = 'TaskPriorityEnum'
                else:
                    suggested_enum = 'PriorityEnum'
            
            elif field_name.lower() == 'tlp':
                if app_name == 'alerts':
                    suggested_enum = 'AlertTLPEnum'
                elif app_name == 'incidents':
                    suggested_enum = 'IncidentTLPEnum'
                elif app_name == 'observables':
                    suggested_enum = 'ObservableTLPEnum'
                else:
                    suggested_enum = 'TLPEnum'
            
            elif field_name.lower() == 'pap':
                if app_name == 'alerts':
                    suggested_enum = 'AlertPAPEnum'
                elif app_name == 'incidents':
                    suggested_enum = 'IncidentPAPEnum'
                else:
                    suggested_enum = 'PAPEnum'
            
            elif field_name.lower() == 'type':
                if app_name == 'observables':
                    suggested_enum = 'ObservableTypeEnum'
                else:
                    suggested_enum = f"{model_name}TypeEnum"
            
            elif field_name.lower() == 'category':
                if app_name == 'observables':
                    suggested_enum = 'ObservableCategoryEnum'
                else:
                    suggested_enum = f"{model_name}CategoryEnum"
            
            else:
                suggested_enum = f"{model_name}{field_name.capitalize()}Enum"
            
            # Sugestão de substituição
            module_prefix = app_name
            
            # Determinar import correto
            if suggested_enum in [
                'StatusEnum', 'PriorityEnum', 'TLPEnum', 'PAPEnum', 'ActionTypeEnum'
            ]:
                import_from = "api.v1.common.enums"
            else:
                import_from = f"api.v1.{module_prefix}.enums"
            
            print(f"\n💡 Sugestão de substituição:")
            print(f"   1. Adicionar import:")
            print(f"      from {import_from} import {suggested_enum}")
            print(f"      from api.core.utils.enum_utils import enum_to_choices")
            print(f"   2. Substituir choices no campo:")
            print(f"      {field_name} = models.XXXField(..., choices=enum_to_choices({suggested_enum}), ...)")
        
        if not found_choices:
            print(f"✅ Nenhum choice encontrado no modelo {model_name}.")
    
    except Exception as e:
        print(f"❌ Erro durante análise: {str(e)}")


def main():
    if len(sys.argv) < 3:
        print(f"Uso: {sys.argv[0]} <app_name> <model_name>")
        sys.exit(1)
    
    app_name = sys.argv[1]
    model_name = sys.argv[2]
    
    print(f"🔍 Analisando modelo {model_name} no app {app_name}")
    print_model_choices(app_name, model_name)


if __name__ == "__main__":
    main()
