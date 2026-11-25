ALIASES = {'cepat': 'fast', 'seimbang': 'balanced', 'akurat': 'best'}
FORMATS = {'text': ('txt',), 'subtitle': ('srt',), 'both': ('txt', 'srt'),
           'all': ('txt', 'srt', 'vtt', 'json', 'md')}
# Approximate download / working RAM, not hardware guarantees.
MODELS = {
    'tiny': ('75 MB', '~1 GB', 'Paling cepat', 'Uji pemasangan'),
    'base': ('145 MB', '~1 GB', 'Cepat', 'Draf; periksa nama dan angka'),
    'small': ('485 MB', '~2 GB', 'Seimbang', 'Default untuk bahasa Indonesia'),
    'turbo': ('1,6 GB', '~4 GB', 'Lebih lambat di CPU', 'Detail lebih baik; terjemahan memakai large-v3'),
    'large-v3': ('3,1 GB', '~8 GB', 'Berat', 'Butuh memori lebih besar'),
}


def quality(value):
    value = ALIASES.get(value, value)
    if value not in ('fast', 'balanced', 'best'):
        raise ValueError('Kualitas harus fast/cepat, balanced/seimbang, atau best/akurat.')
    return value


def model_for(value, device='cpu', vram_mb=0, translate=False):
    value = quality(value)
    if value == 'best':
        return 'large-v3' if translate or (device == 'cuda' and vram_mb >= 10000) else 'turbo'
    return {'fast': 'base', 'balanced': 'small'}[value]
