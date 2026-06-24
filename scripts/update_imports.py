import os

base_dir = r'd:\desarrollo-uni\formación-festio'
target_dirs = [os.path.join(base_dir, 'app'), os.path.join(base_dir, 'scripts'), os.path.join(base_dir, 'tests')]

replacements = {
    'app.domain.common.enums': 'app.domain.common.enums',
    'app.domain.usuarios.models': 'app.domain.usuarios.models',
    'app.domain.catalogo.models': 'app.domain.catalogo.models',
    'app.domain.reservas.models': 'app.domain.reservas.models',
    'app.domain.disponibilidad.models': 'app.domain.disponibilidad.models',
    'app.domain.pagos.models': 'app.domain.pagos.models',
    'app.domain.personal.models': 'app.domain.personal.models',
    'app.domain.notificaciones.models': 'app.domain.notificaciones.models',
    'app.domain.resenas.models': 'app.domain.resenas.models',
    
    'app.domain.common.enums': 'app.domain.common.enums',
    'app.domain.usuarios.schemas': 'app.domain.usuarios.schemas',
    'app.domain.catalogo.schemas': 'app.domain.catalogo.schemas',
    'app.domain.reservas.schemas': 'app.domain.reservas.schemas',
    'app.domain.disponibilidad.schemas': 'app.domain.disponibilidad.schemas',
    'app.domain.pagos.schemas': 'app.domain.pagos.schemas',
    'app.domain.personal.schemas': 'app.domain.personal.schemas',
    'app.domain.notificaciones.schemas': 'app.domain.notificaciones.schemas',
    'app.domain.resenas.schemas': 'app.domain.resenas.schemas',
    'app.domain.chat.schemas': 'app.domain.chat.schemas',
    
    'import app.domain.all_models': 'import app.domain.all_models'
}

for t_dir in target_dirs:
    for root, dirs, files in os.walk(t_dir):
        if '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old, new in replacements.items():
                    new_content = new_content.replace(old, new)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f'Updated {filepath}')

print("Done updating imports")
