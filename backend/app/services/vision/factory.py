"""Resolve configured acceleration with a visible fallback; no model substitutions."""
from ...runtime_config import ROOT
from . import UltralyticsPeople

def resolve_acceleration(requested='auto', torch_module=None):
    if torch_module is None: import torch as torch_module
    cuda=torch_module.cuda.is_available()
    mps=hasattr(torch_module.backends,'mps') and torch_module.backends.mps.is_available()
    if requested not in ('auto','cuda','mps','cpu'): raise ValueError('Unsupported vision acceleration')
    if requested=='auto': return ('cuda:0' if cuda else 'mps' if mps else 'cpu'),None
    available=requested=='cpu' or (requested=='cuda' and cuda) or (requested=='mps' and mps)
    if available: return ('cuda:0' if requested=='cuda' else requested),None
    return 'cpu',f'{requested} unavailable in this interpreter; using CPU'

def create_person_tracker(config):
    device,warning=resolve_acceleration(config['vision']['acceleration'])
    weights=ROOT/'models/vision/yolo26n.pt'
    if not weights.is_file(): raise FileNotFoundError('Run bootstrap_models.py --perception')
    return UltralyticsPeople(weights,device=device),warning
