"""Form labels and explicit unit choices; no mathematical calculations."""

MODES = {
    'air': 'Psicrometría', 'conversion': 'Conversiones', 'geometry': 'Geometría',
    'tray': 'Charolas', 'extruded': 'Sólidos extruidos',
    'continuous': 'Secador continuo', 'rotary': 'Secador rotatorio',
}
MODE_DETAILS = {
    'air': {
        'eyebrow': 'ESTADO DEL AIRE',
        'title': MODES['air'],
        'description': 'Resuelve el estado completo del aire a partir de dos propiedades independientes.',
    },
    'conversion': {
        'eyebrow': 'SISTEMA DE UNIDADES',
        'title': MODES['conversion'],
        'description': 'Convierte magnitudes con factores centralizados y temperatura absoluta explícita.',
    },
    'geometry': {
        'eyebrow': 'SUPERFICIE DE SECADO',
        'title': MODES['geometry'],
        'description': 'Calcula área total y volumen para las geometrías usadas en sólidos extruidos.',
    },
    'tray': {
        'eyebrow': 'SECADO POR LOTES',
        'title': MODES['tray'],
        'description': 'Obtén masa evaporada, transferencia convectiva y tiempo crítico de charola.',
    },
    'extruded': {
        'eyebrow': 'LECHO DE PARTÍCULAS',
        'title': MODES['extruded'],
        'description': 'Combina geometría, porosidad y Reynolds para estimar el tiempo crítico.',
    },
    'continuous': {
        'eyebrow': 'PERFIL AXIAL',
        'title': MODES['continuous'],
        'description': 'Genera el perfil psicrométrico y la longitud del secador continuo.',
    },
    'rotary': {
        'eyebrow': 'BALANCE INTEGRAL',
        'title': MODES['rotary'],
        'description': 'Resuelve balances de calor y masa, diámetro y longitud del secador rotatorio.',
    },
}
PROPERTIES = {'dry_bulb': 'Bulbo seco', 'wet_bulb': 'Bulbo húmedo',
              'dew_point': 'Punto de rocío', 'relative_humidity': 'Humedad relativa (%)',
              'humidity_ratio': 'Humedad absoluta (lb agua/lb aire seco)'}
SHAPES = {
    'cylinder': ('Cilindro', 'CILINDRO.png'), 'sphere': ('Esfera', 'ESFERA.jpg'),
    'cube': ('Cubo', 'CUBO.jpg'), 'box': ('Paralelepípedo', 'PARALELEPIPEDO.jpg'),
    'cone': ('Cono', 'CONO.jpg'),
    'square_pyramid': ('Pirámide cuadrada', 'PIRAMIDE BASE CUADRADA.jpg'),
    'triangular_prism': ('Prisma triangular', 'PRISMA TRIANGULAR.jpg'),
    'quadrangular_prism': ('Prisma cuadrangular', 'PRISMA CUADRIANGULAR RECTO.jpg'),
    'frustum': ('Tronco de cono', 'CONO DE TRONCO CIRCULAR RECTO.jpg'),
    'hemisphere': ('Hemisferio', 'HEMISFERIO.jpg'),
    'hexagonal_prism': ('Prisma hexagonal', 'MRISMA HEXAGONAL.jpg'),
    'other': ('Otra', ''),
}
DIMENSION_LABELS = {'r': 'Radio r', 'R': 'Radio R', 'h': 'Altura h',
                    'a': 'Lado a', 'b': 'Base / lado b',
                    'length': 'Longitud del prisma'}
