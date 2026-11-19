"""Optional experimental pretrained model adapter. Requires internet for initial model download."""
import numpy as np
from PIL import Image

REPO = 'Pranilllllll/segformer-satellite-segementation'

def classify_ai(rgb, mode):
    import torch
    from transformers import AutoImageProcessor, AutoModelForSemanticSegmentation
    import torch.nn.functional as F
    processor=AutoImageProcessor.from_pretrained(REPO)
    model=AutoModelForSemanticSegmentation.from_pretrained(REPO)
    model.eval()
    inputs=processor(images=Image.fromarray(rgb),return_tensors='pt')
    with torch.no_grad(): logits=model(**inputs).logits
    logits=F.interpolate(logits, size=rgb.shape[:2],mode='bilinear',align_corners=False)
    preds=logits.argmax(dim=1)[0].cpu().numpy()
    labels={int(k):str(v).lower() for k,v in model.config.id2label.items()}
    if mode=='Forest':
        ids=[k for k,v in labels.items() if 'forest' in v or 'tree' in v]
    else:
        ids=[k for k,v in labels.items() if 'residential' in v or 'built' in v or 'road' in v or 'urban' in v]
    if not ids: raise ValueError(f'Model labels do not include the requested land type. Available: {labels}')
    return np.isin(preds,ids)
