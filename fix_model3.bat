@echo off
setlocal
echo [Rakkun] Restaurando model3.json...

py -c "
import json, os

base = os.path.dirname(os.path.abspath('fix_model3.bat'))
target = os.path.join(base, 'seps_web', 'static', 'live2d', 'rakkun', 'rakkun.model3.json')

data = {
    'Version': 3,
    'FileReferences': {
        'Moc': 'rakkun_v2.moc3',
        'Textures': [f'rakkun.4096/texture_{i:02d}.png' for i in range(11)],
        'Physics': 'rakkun.physics3.json',
        'DisplayInfo': 'rakkun.cdi3.json',
        'Expressions': [
            {'Name': 'maid_formal',       'File': 'expressions/maid_formal.exp3.json'},
            {'Name': 'maid',              'File': 'expressions/maid.exp3.json'},
            {'Name': 'excited',           'File': 'expressions/excited.exp3.json'},
            {'Name': 'shy',               'File': 'expressions/shy.exp3.json'},
            {'Name': 'nervous',           'File': 'expressions/nervous.exp3.json'},
            {'Name': 'sad',               'File': 'expressions/sad.exp3.json'},
            {'Name': 'heh',               'File': 'expressions/heh.exp3.json'},
            {'Name': 'sing',              'File': 'expressions/sing.exp3.json'},
            {'Name': 'confused',          'File': 'expressions/confused.exp3.json'},
            {'Name': 'angry',             'File': 'expressions/angry.exp3.json'},
            {'Name': 'embarrased',        'File': 'expressions/embarrased.exp3.json'},
            {'Name': 'scared',            'File': 'expressions/scared.exp3.json'},
            {'Name': 'mad',               'File': 'expressions/mad.exp3.json'},
            {'Name': 'hun',               'File': 'expressions/hun.exp3.json'},
            {'Name': 'wink',              'File': 'expressions/wink.exp3.json'},
            {'Name': 'tongue',            'File': 'expressions/tongue.exp3.json'},
            {'Name': 'cheekpuff',         'File': 'expressions/cheekpuff.exp3.json'},
            {'Name': 'yandere',           'File': 'expressions/yandere.exp3.json'},
            {'Name': 'outfit1',           'File': 'expressions/outfit1.exp3.json'},
            {'Name': 'jacket',            'File': 'expressions/jacket.exp3.json'},
            {'Name': 'cap',               'File': 'expressions/cap.exp3.json'},
            {'Name': 'ears',              'File': 'expressions/ears.exp3.json'},
            {'Name': 'mask',              'File': 'expressions/mask.exp3.json'},
            {'Name': 'gloves',            'File': 'expressions/gloves.exp3.json'},
            {'Name': 'shoe',              'File': 'expressions/shoe.exp3.json'},
            {'Name': 'tailonoff',         'File': 'expressions/tailonoff.exp3.json'},
            {'Name': 'draw',              'File': 'expressions/draw.exp3.json'},
            {'Name': 'game',              'File': 'expressions/game.exp3.json'},
            {'Name': 'mascot',            'File': 'expressions/mascot.exp3.json'},
            {'Name': 'mizugi',            'File': 'expressions/mizugi.exp3.json'},
            {'Name': 'darkmodemizugi',    'File': 'expressions/darkmodemizugi.exp3.json'},
            {'Name': 'mizugitransparent', 'File': 'expressions/mizugitransparent.exp3.json'},
            {'Name': 'sunglasses',        'File': 'expressions/sunglasses.exp3.json'},
            {'Name': 'ek',                'File': 'expressions/ek.exp3.json'},
            {'Name': 'toes',              'File': 'expressions/toes.exp3.json'},
            {'Name': 'ahegao',            'File': 'expressions/ahegao.exp3.json'},
        ],
        'Motions': {
            'idle':    [{'File': 'motions/idle.motion3.json',    'FadeInTime': 0.5, 'FadeOutTime': 0.5}],
            'dance':   [{'File': 'motions/dance.motion3.json',   'FadeInTime': 0.5, 'FadeOutTime': 0.5}],
            'karaoke': [{'File': 'motions/karaoke.motion3.json', 'FadeInTime': 0.5, 'FadeOutTime': 0.5}],
            'pentab':  [{'File': 'motions/pentab.motion3.json',  'FadeInTime': 0.5, 'FadeOutTime': 0.5}],
        }
    },
    'Groups': [
        {'Target': 'Parameter', 'Name': 'LipSync',  'Ids': []},
        {'Target': 'Parameter', 'Name': 'EyeBlink', 'Ids': []},
    ]
}

with open(target, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent='\t', ensure_ascii=False)

print('[OK] ' + target)
print('     Textures:    11')
print('     Expressions: ' + str(len(data['FileReferences']['Expressions'])))
print('     Motions:     ' + str(list(data['FileReferences']['Motions'].keys())))
"

if errorlevel 1 (
    echo [ERROR] Fallo el script. Asegurate de tener Python instalado ^(py --version^).
) else (
    echo.
    echo Listo. Recarga la pagina del avatar en el navegador.
)
echo.
pause
