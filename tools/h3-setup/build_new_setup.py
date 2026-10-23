# -*- coding: utf-8 -*-
import json, re, os
SRC = r"e:\trae_workspace\aigc\work\ic\h3-setup.container.html"
OUT = r"e:\trae_workspace\aigc\work\ic\h3-setup.new.html"
H3BASE = "http://140.207.205.59:18188"
IMGBASE = "http://140.207.205.59:18422"

VIDEO_TAIL = r"""
let sub;
try { sub = await (await fetch(base + '/prompt', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: g }) })).json(); }
catch (e) { throw new Error('无法连接 ComfyUI: ' + e.message); }
const pid = sub && sub.prompt_id;
if (!pid) { const em = (sub && sub.error && (sub.error.message || sub.error.type)) || JSON.stringify(sub).slice(0, 300); throw new Error('提交失败: ' + em); }
let entry = null; const deadline = Date.now() + 60 * 60 * 1000;
while (Date.now() < deadline) {
  if (signal && signal.aborted) { (async function () { try { const q = await (await fetch(base + '/queue')).json(); const run = ((q && q.queue_running) || []).map(function (x) { return x[1]; }); if (run.indexOf(pid) >= 0) { await fetch(base + '/interrupt', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }); } else { await fetch(base + '/queue', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ delete: [pid] }) }); } } catch (e) {} })(); throw new DOMException('Aborted', 'AbortError'); }
  try { const hd = await (await fetch(base + '/history/' + pid)).json(); if (hd && hd[pid]) { entry = hd[pid]; break; } } catch (e) {}
  await new Promise(function (r) { setTimeout(r, 5000); });
}
if (!entry) throw new Error('等待成片超时（60 分钟）');
const st = (entry.status && entry.status.status_str) || 'unknown';
if (st !== 'success') { let mm = '生成失败(' + st + ')'; const ms = (entry.status && entry.status.messages) || []; for (let i = 0; i < ms.length; i++) { if (ms[i][0] === 'execution_error' && ms[i][1] && ms[i][1].exception_message) { mm = ms[i][1].exception_message.slice(0, 400); break; } } throw new Error(mm); }
const outs = entry.outputs || {}; let url = null;
for (const k in outs) { const arr = (outs[k] && (outs[k].videos || outs[k].images || outs[k].gifs)) || []; const mp4 = arr.find(function (x) { return /\.(mp4|webm|gif)$/i.test(x.filename); }); if (mp4) { url = base + '/view?filename=' + encodeURIComponent(mp4.filename) + '&subfolder=' + encodeURIComponent(mp4.subfolder || '') + '&type=' + encodeURIComponent(mp4.type || 'output'); break; } }
if (!url) throw new Error('ComfyUI 未返回视频');
return url;
"""

IMAGE_TAIL = r"""
let sub;
try { sub = await (await fetch(base + '/prompt', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: g }) })).json(); }
catch (e) { throw new Error('无法连接 ComfyUI: ' + e.message); }
const pid = sub && sub.prompt_id;
if (!pid) { const em = (sub && sub.error && (sub.error.message || sub.error.type)) || JSON.stringify(sub).slice(0, 300); throw new Error('提交失败: ' + em); }
let entry = null; const deadline = Date.now() + 30 * 60 * 1000;
while (Date.now() < deadline) {
  if (signal && signal.aborted) { (async function () { try { const q = await (await fetch(base + '/queue')).json(); const run = ((q && q.queue_running) || []).map(function (x) { return x[1]; }); if (run.indexOf(pid) >= 0) { await fetch(base + '/interrupt', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }); } else { await fetch(base + '/queue', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ delete: [pid] }) }); } } catch (e) {} })(); throw new DOMException('Aborted', 'AbortError'); }
  try { const hd = await (await fetch(base + '/history/' + pid)).json(); if (hd && hd[pid]) { entry = hd[pid]; break; } } catch (e) {}
  await new Promise(function (r) { setTimeout(r, 4000); });
}
if (!entry) throw new Error('等待超时（30 分钟）');
const st = (entry.status && entry.status.status_str) || 'unknown';
if (st !== 'success') { let mm = '生成失败(' + st + ')'; const ms = (entry.status && entry.status.messages) || []; for (let i = 0; i < ms.length; i++) { if (ms[i][0] === 'execution_error' && ms[i][1] && ms[i][1].exception_message) { mm = ms[i][1].exception_message.slice(0, 400); break; } } throw new Error(mm); }
const outs = entry.outputs || {}; const files = [];
for (const k in outs) { if (outs[k] && outs[k].images) files.push.apply(files, outs[k].images); }
if (!files.length) throw new Error('ComfyUI 未返回图片');
function toB64(buf) { const bytes = new Uint8Array(buf); const CH = 0x8000; let s = ''; for (let i = 0; i < bytes.length; i += CH) s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH)); return btoa(s); }
const results = [];
for (let i = 0; i < files.length && i < 4; i++) {
  const f = files[i];
  const vu = base + '/view?filename=' + encodeURIComponent(f.filename) + '&subfolder=' + encodeURIComponent(f.subfolder || '') + '&type=' + encodeURIComponent(f.type || 'output');
  const ir = await fetch(vu); if (!ir.ok) throw new Error('获取图片失败: ' + ir.status);
  const ab = await ir.arrayBuffer(); const ct = (ir.headers.get('Content-Type') || 'image/png').split(';')[0];
  results.push('data:' + ct + ';base64,' + toB64(ab));
}
return results;
"""

UPIMG = r"""
async function fitRef(src){try{var im=await new Promise(function(res,rej){var o=new Image();o.onload=function(){res(o);};o.onerror=function(){rej(new Error('x'));};o.src=src;});var ow=im.naturalWidth,oh=im.naturalHeight;if(!ow||!oh)return src;var s=1,mn=Math.min(ow,oh),mx=Math.max(ow,oh);if(mn<256)s=256/mn;if(mx*s>5760)s=Math.min(s,5760/mx);var w=Math.max(1,Math.round(ow*s)),h=Math.max(1,Math.round(oh*s)),cw=w,ch=h,ox=0,oy=0,r=w/h;if(r>2.5){ch=Math.round(w/2.5);oy=Math.round((ch-h)/2);}else if(r<0.4){cw=Math.round(h*0.4);ox=Math.round((cw-w)/2);}if(w===ow&&h===oh&&cw===ow&&ch===oh)return src;var cv=document.createElement('canvas');cv.width=cw;cv.height=ch;var cx=cv.getContext('2d');cx.fillStyle='#000';cx.fillRect(0,0,cw,ch);cx.drawImage(im,ox,oy,w,h);return cv.toDataURL('image/png');}catch(e){return src;}} async function upImg(dataUrl, name) {
  const b = await (await fetch(String(dataUrl))).blob();
  const form = new FormData();
  form.append('image', new Blob([b], { type: 'image/png' }), name);
  form.append('overwrite', 'true');
  const r = await (await fetch(base + '/upload/image', { method: 'POST', body: form })).json();
  if (!r || !r.name) throw new Error('图片上传失败: ' + JSON.stringify(r).slice(0, 150));
  return r.name;
}
const __imgs = (Array.isArray(images) ? images : []).filter(function (x) { return typeof x === 'string' && x.indexOf('data:image') === 0; });
"""

VLLM = (r"""// vllm-omni 视频（文生/图生/参考生）— 经 ComfyUI VllmOmniH3 节点
const base = (baseUrl || '').replace(/\/+$/, '');
const p = params || {};
const isR2V = /参考/.test(model), isI2V = /图生/.test(model);
const task = isR2V ? 'ref2va' : (isI2V ? 'fl2va' : 't2va');
const SVR = isR2V ? 'http://127.0.0.1:8094' : 'http://127.0.0.1:8095';
function r32(v) { return Math.max(256, Math.round(v / 32) * 32); }
let w = 1344, h = 768;
const szRaw = String(p.size || '');
if (/^\d+\s*[xX]\s*\d+$/.test(szRaw)) { const t = szRaw.split(/[xX]/); w = parseInt(t[0], 10); h = parseInt(t[1], 10); }
else if (/^\d+\s*:\s*\d+$/.test(szRaw)) { const t = szRaw.split(':'); const a = parseInt(t[0], 10) || 16, b = parseInt(t[1], 10) || 9; if (a >= b) { h = 768; w = r32(768 * a / b); } else { w = 768; h = r32(768 * b / a); } }
w = r32(w); h = r32(h);
let secs = Number(p.seconds) > 0 ? Number(p.seconds) : 6; if (secs < 4) secs = 4; if (secs > 15) secs = 15;
const FPS = 24;
let steps = 8, loraScale = 0.7, intId = 2, flowShift = 6.0, seed = Math.floor(Math.random() * 1e15);
let clean = String(prompt || '');
const ovRe = /\[(steps|lora|seed|seconds|flow|int|refedge)\s*[=:]\s*([^\]]+?)\]/gi;
let mm, ov = {};
while ((mm = ovRe.exec(clean))) { ov[mm[1].toLowerCase()] = mm[2].trim(); }
clean = clean.replace(ovRe, '').replace(/[ \t]{2,}/g, ' ').trim();
if (ov.steps) { const n = parseInt(ov.steps, 10); if (n > 0 && n <= 50) steps = n; }
if (ov.lora) { const n = parseFloat(ov.lora); if (n > 0 && n <= 2) loraScale = n; }
if (ov.flow) { const n = parseFloat(ov.flow); if (n > 0 && n <= 20) flowShift = n; }
if (ov.int) { const n = parseInt(ov.int, 10); if (n >= 0) intId = n; }
if (ov.seconds) { const n = parseFloat(ov.seconds); if (n >= 4 && n <= 15) secs = n; }
if (ov.seed && /^\d+$/.test(ov.seed)) seed = parseInt(ov.seed, 10);
const numFrames = Math.max(4 * FPS, Math.min(15 * FPS, Math.round(secs * FPS))); let refEdge = /省流/.test(model) ? 1024 : 0; if (ov.refedge) { var _re = parseInt(ov.refedge, 10); if (_re >= 512 && _re <= 2048) refEdge = _re; }
const bsa = /BSA/.test(model) ? 0.5 : 0;
const g = {};
""" + UPIMG + r"""
const node = { class_type: 'VllmOmniH3', inputs: { prompt: clean, task: task, server_url: SVR, width: w, height: h, num_frames: numFrames, fps: FPS, seed: seed, steps: steps, lora_file: '', lora_scale: loraScale, int_id: intId, flow_shift: flowShift, aspect_ratio: (w >= h ? '16:9' : '9:16'), reference_short_edge: refEdge, bsa_sparsity: bsa } };
g['200'] = node;
if (isI2V) {
  if (!__imgs.length) throw new Error('图生视频需要至少 1 张图片（画布上选中图片作首帧）');
  const nm = await upImg(await fitRef(__imgs[0]), 'canvas_i2v_first.png');
  g['20'] = { class_type: 'LoadImage', inputs: { image: nm } }; node.inputs.first_frame = ['20', 0];
} else if (isR2V) {
  if (!__imgs.length) throw new Error('参考生视频需要 1~9 张参考图');
  let prev = null;
  for (let i = 0; i < __imgs.length && i < 9; i++) {
    const nm = await upImg(await fitRef(__imgs[i]), 'canvas_r2v_' + i + '.png');
    const nid = String(30 + i); g[nid] = { class_type: 'LoadImage', inputs: { image: nm } };
    if (prev === null) prev = nid; else { const bid = String(310 + i); g[bid] = { class_type: 'ImageBatch', inputs: { image1: [prev, 0], image2: [nid, 0] } }; prev = bid; }
  }
  if (prev !== null) node.inputs.ref_images = [prev, 0];
}
g['14'] = { class_type: 'CreateVideo', inputs: { images: ['200', 0], audio: ['200', 1], fps: FPS } };
g['15'] = { class_type: 'SaveVideo', inputs: { video: ['14', 0], filename_prefix: 'video/MiniMax_H3_vllm', format: 'auto', codec: 'auto' } };
""" + VIDEO_TAIL)

# vllm-omni 视频 · LoRA 加速版：与 VLLM 相同，但按任务挂载官方 4 步 LoRA（turbo/flashgen）
# 注意：服务端已对齐 upstream #7219（num_inference_steps = 去噪评估次数）—— 4 步 LoRA 一律取 4（不再按任务取 4/5）
# LoRA 对应配置（服务端路径）：t2va/fl2va→fl2v turbo、ref2va→ref2v turbo（文生复用 fl2v turbo）
VLLM_LORA = (r"""// vllm-omni 视频 · LoRA 加速版（文生/图生/参考生）— 经 ComfyUI VllmOmniH3 节点（4 步 turbo LoRA）
const base = (baseUrl || '').replace(/\/+$/, '');
const p = params || {};
const isR2V = /参考/.test(model), isI2V = /图生/.test(model);
const task = isR2V ? 'ref2va' : (isI2V ? 'fl2va' : 't2va');
const SVR = isR2V ? 'http://127.0.0.1:8094' : 'http://127.0.0.1:8095';
// LoRA 对应配置：按任务挂载官方 4 步 LoRA（t2va 复用 fl2v turbo；路径为服务端可见路径）
const LORA = {
  t2va: '/mnt/hcufs/tools/minimax-h3/lora_official/minimax_h3_fl2v_turbo_4step_v1.0_768p_bf16.safetensors',
  fl2va: '/mnt/hcufs/tools/minimax-h3/lora_official/minimax_h3_fl2v_turbo_4step_v1.0_768p_bf16.safetensors',
  ref2va: '/mnt/hcufs/tools/minimax-h3/lora_official/minimax_h3_ref2v_turbo_4step_v0.1_bf16.safetensors'
};
function r32(v) { return Math.max(256, Math.round(v / 32) * 32); }
let w = 1344, h = 768;
const szRaw = String(p.size || '');
if (/^\d+\s*[xX]\s*\d+$/.test(szRaw)) { const t = szRaw.split(/[xX]/); w = parseInt(t[0], 10); h = parseInt(t[1], 10); }
else if (/^\d+\s*:\s*\d+$/.test(szRaw)) { const t = szRaw.split(':'); const a = parseInt(t[0], 10) || 16, b = parseInt(t[1], 10) || 9; if (a >= b) { h = 768; w = r32(768 * a / b); } else { w = 768; h = r32(768 * b / a); } }
w = r32(w); h = r32(h);
let secs = Number(p.seconds) > 0 ? Number(p.seconds) : 6; if (secs < 4) secs = 4; if (secs > 15) secs = 15;
const FPS = 24;
let steps = 4, loraScale = 0.7, intId = (isR2V ? 12 : 11), flowShift = (isR2V ? 12.0 : 6.0), seed = Math.floor(Math.random() * 1e15);
let clean = String(prompt || '');
const ovRe = /\[(steps|lora|seed|seconds|flow|int|refedge)\s*[=:]\s*([^\]]+?)\]/gi;
let mm, ov = {};
while ((mm = ovRe.exec(clean))) { ov[mm[1].toLowerCase()] = mm[2].trim(); }
clean = clean.replace(ovRe, '').replace(/[ \t]{2,}/g, ' ').trim();
if (ov.steps) { const n = parseInt(ov.steps, 10); if (n > 0 && n <= 50) steps = n; }
if (ov.lora) { const n = parseFloat(ov.lora); if (n > 0 && n <= 2) loraScale = n; }
if (ov.flow) { const n = parseFloat(ov.flow); if (n > 0 && n <= 20) flowShift = n; }
if (ov.int) { const n = parseInt(ov.int, 10); if (n >= 0) intId = n; }
if (ov.seconds) { const n = parseFloat(ov.seconds); if (n >= 4 && n <= 15) secs = n; }
if (ov.seed && /^\d+$/.test(ov.seed)) seed = parseInt(ov.seed, 10);
const numFrames = Math.max(4 * FPS, Math.min(15 * FPS, Math.round(secs * FPS))); let refEdge = /省流/.test(model) ? 1024 : 0; if (ov.refedge) { var _re = parseInt(ov.refedge, 10); if (_re >= 512 && _re <= 2048) refEdge = _re; }
const bsa = /BSA/.test(model) ? 0.5 : 0;
const g = {};
""" + UPIMG + r"""
const node = { class_type: 'VllmOmniH3', inputs: { prompt: clean, task: task, server_url: SVR, width: w, height: h, num_frames: numFrames, fps: FPS, seed: seed, steps: steps, lora_file: LORA[task], lora_scale: loraScale, int_id: intId, flow_shift: flowShift, aspect_ratio: (w >= h ? '16:9' : '9:16'), reference_short_edge: refEdge, bsa_sparsity: bsa } };
g['200'] = node;
if (isI2V) {
  if (!__imgs.length) throw new Error('图生视频需要至少 1 张图片（画布上选中图片作首帧）');
  const nm = await upImg(await fitRef(__imgs[0]), 'canvas_i2v_first.png');
  g['20'] = { class_type: 'LoadImage', inputs: { image: nm } }; node.inputs.first_frame = ['20', 0];
} else if (isR2V) {
  if (!__imgs.length) throw new Error('参考生视频需要 1~9 张参考图');
  let prev = null;
  for (let i = 0; i < __imgs.length && i < 9; i++) {
    const nm = await upImg(await fitRef(__imgs[i]), 'canvas_r2v_' + i + '.png');
    const nid = String(30 + i); g[nid] = { class_type: 'LoadImage', inputs: { image: nm } };
    if (prev === null) prev = nid; else { const bid = String(310 + i); g[bid] = { class_type: 'ImageBatch', inputs: { image1: [prev, 0], image2: [nid, 0] } }; prev = bid; }
  }
  if (prev !== null) node.inputs.ref_images = [prev, 0];
}
g['14'] = { class_type: 'CreateVideo', inputs: { images: ['200', 0], audio: ['200', 1], fps: FPS } };
g['15'] = { class_type: 'SaveVideo', inputs: { video: ['14', 0], filename_prefix: 'video/MiniMax_H3_vllm_lora', format: 'auto', codec: 'auto' } };
""" + VIDEO_TAIL)

SR_IMG = (r"""// SeedVR2 图片超分（3B / 7B，按模型名自动选择权重）
const base = (baseUrl || '').replace(/\/+$/, '');
const p = params || {};
const UNET = /7B/i.test(model) ? 'seedvr2_7b_int8_convrot.safetensors' : 'seedvr2_3b_int8_convrot.safetensors';
// 目标分辨率：内联 [longer=|megapixels=|scale=] > 创作台 resolution(清晰度) > size(WxH) > quality > 倍数(默认2)
let clean = String(prompt || '');
let longer = 0, mp = 0, mult = 0;
{ const re = /\[(longer|megapixels|scale)\s*[=:]\s*([\d.]+)\]/gi; let mm;
  while ((mm = re.exec(clean))) { const k = mm[1].toLowerCase(), v = parseFloat(mm[2]);
    if (k === 'longer' && v >= 64 && v <= 16384) longer = Math.round(v);
    else if (k === 'megapixels' && v >= 0.01 && v <= 16) mp = v;
    else if (k === 'scale' && v >= 1 && v <= 8) mult = v; }
  clean = clean.replace(re, '').trim(); }
const LONG_EDGE = { '480': 854, '540': 960, '720': 1280, '1080': 1920, '1440': 2560, '2048': 2048, '2k': 2560, '2160': 3840, '4k': 3840 };
const QUAL_LONG = { low: 1280, standard: 1280, medium: 2048, hd: 2048, auto: 1920, high: 3840 };
if (!longer && !mp && !mult) { const rk = String(p.resolution || '').trim().toLowerCase().replace(/p$/, ''); if (LONG_EDGE[rk]) longer = LONG_EDGE[rk]; }
if (!longer && !mp && !mult) { const sz = String(p.size || '').match(/^(\d+)\s*[x\u00d7]\s*(\d+)$/); if (sz) { const a = Number(sz[1]), b = Number(sz[2]); if (a >= 64 && b >= 64) longer = Math.max(a, b); } }
if (!longer && !mp && !mult) { const q = String(p.quality || '').trim().toLowerCase(); if (QUAL_LONG[q]) longer = QUAL_LONG[q]; }
if (!longer && !mp && !mult) { mult = 2; const sc = String(p.scale || '').trim(); if (/^[\d.]+$/.test(sc)) { const n = parseFloat(sc); if (n >= 1 && n <= 8) mult = n; } }
function srResizeNode(srcRef) {
  if (longer) return { class_type: 'ResizeImageMaskNode', inputs: { input: srcRef, resize_type: 'scale longer dimension', scale_method: 'lanczos', 'resize_type.longer_size': longer } };
  if (mp) return { class_type: 'ResizeImageMaskNode', inputs: { input: srcRef, resize_type: 'scale total pixels', scale_method: 'lanczos', 'resize_type.megapixels': mp } };
  return { class_type: 'ResizeImageMaskNode', inputs: { input: srcRef, resize_type: 'scale by multiplier', scale_method: 'lanczos', 'resize_type.multiplier': mult } };
}
""" + UPIMG + r"""
if (!__imgs.length) throw new Error('超分需要 1 张图片（画布上选中图片）');
const mainName = await upImg(__imgs[0], 'canvas_sr_in.png');
const seed = Math.floor(Math.random() * 1e15);
const g = {};
g['108'] = { class_type: 'UNETLoader', inputs: { unet_name: UNET, weight_dtype: 'default' } };
g['107'] = { class_type: 'VAELoader', inputs: { vae_name: 'seedvr2_ema_vae_fp16.safetensors' } };
g['1'] = { class_type: 'LoadImage', inputs: { image: mainName } };
g['111'] = srResizeNode(['1', 0]);
g['112'] = { class_type: 'SeedVR2Preprocess', inputs: { resized_images: ['111', 0] } };
g['106'] = { class_type: 'VAEEncodeTiled', inputs: { pixels: ['112', 0], vae: ['107', 0], tile_size: 512, overlap: 128, temporal_size: 64, temporal_overlap: 8 } };
g['114'] = { class_type: 'SeedVR2Conditioning', inputs: { model: ['108', 0], vae_conditioning: ['106', 0] } };
g['109'] = { class_type: 'KSampler', inputs: { model: ['108', 0], seed: seed, steps: 1, cfg: 1, sampler_name: 'euler', scheduler: 'simple', positive: ['114', 0], negative: ['114', 1], latent_image: ['106', 0], denoise: 1 } };
g['110'] = { class_type: 'VAEDecodeTiled', inputs: { samples: ['109', 0], vae: ['107', 0], tile_size: 512, overlap: 128, temporal_size: 64, temporal_overlap: 8 } };
g['113'] = { class_type: 'SeedVR2PostProcessing', inputs: { images: ['110', 0], original_resized_images: ['111', 0], color_correction_method: 'none' } };
g['20'] = { class_type: 'SaveImage', inputs: { images: ['113', 0], filename_prefix: 'canvas_sr' } };
""" + IMAGE_TAIL)

SR_VID = (r"""// SeedVR2 视频超分（3B / 7B）。输入：params.videoFile 或提示词中的文件名（须已在 ComfyUI input 目录）
const base = (baseUrl || '').replace(/\/+$/, '');
const p = params || {};
const UNET = /7B/i.test(model) ? 'seedvr2_7b_int8_convrot.safetensors' : 'seedvr2_3b_int8_convrot.safetensors';
let file = String(p.videoFile || p.video || '').trim();
if (!file) { const mm = /([^\s"'，。]+\.(?:mp4|mov|webm|mkv))/i.exec(String(prompt || '')); if (mm) file = mm[1]; }
if (!file) throw new Error('视频超分需要 ComfyUI input 目录中的视频文件名：请在参数里给 params.videoFile，或把文件名写进提示词（如 sr_test.mp4）');
// 目标分辨率：内联 [longer=|megapixels=|scale=] > 创作台 resolution(清晰度) > size(WxH) > quality > 倍数(默认2)
let clean = String(prompt || '');
let longer = 0, mp = 0, mult = 0;
{ const re = /\[(longer|megapixels|scale)\s*[=:]\s*([\d.]+)\]/gi; let mm;
  while ((mm = re.exec(clean))) { const k = mm[1].toLowerCase(), v = parseFloat(mm[2]);
    if (k === 'longer' && v >= 64 && v <= 16384) longer = Math.round(v);
    else if (k === 'megapixels' && v >= 0.01 && v <= 16) mp = v;
    else if (k === 'scale' && v >= 1 && v <= 8) mult = v; }
  clean = clean.replace(re, '').trim(); }
const LONG_EDGE = { '480': 854, '540': 960, '720': 1280, '1080': 1920, '1440': 2560, '2048': 2048, '2k': 2560, '2160': 3840, '4k': 3840 };
const QUAL_LONG = { low: 1280, standard: 1280, medium: 2048, hd: 2048, auto: 1920, high: 3840 };
if (!longer && !mp && !mult) { const rk = String(p.resolution || '').trim().toLowerCase().replace(/p$/, ''); if (LONG_EDGE[rk]) longer = LONG_EDGE[rk]; }
if (!longer && !mp && !mult) { const sz = String(p.size || '').match(/^(\d+)\s*[x\u00d7]\s*(\d+)$/); if (sz) { const a = Number(sz[1]), b = Number(sz[2]); if (a >= 64 && b >= 64) longer = Math.max(a, b); } }
if (!longer && !mp && !mult) { const q = String(p.quality || '').trim().toLowerCase(); if (QUAL_LONG[q]) longer = QUAL_LONG[q]; }
if (!longer && !mp && !mult) { mult = 2; const sc = String(p.scale || '').trim(); if (/^[\d.]+$/.test(sc)) { const n = parseFloat(sc); if (n >= 1 && n <= 8) mult = n; } }
function srResizeNode(srcRef) {
  if (longer) return { class_type: 'ResizeImageMaskNode', inputs: { input: srcRef, resize_type: 'scale longer dimension', scale_method: 'lanczos', 'resize_type.longer_size': longer } };
  if (mp) return { class_type: 'ResizeImageMaskNode', inputs: { input: srcRef, resize_type: 'scale total pixels', scale_method: 'lanczos', 'resize_type.megapixels': mp } };
  return { class_type: 'ResizeImageMaskNode', inputs: { input: srcRef, resize_type: 'scale by multiplier', scale_method: 'lanczos', 'resize_type.multiplier': mult } };
}
const seed = Math.floor(Math.random() * 1e15);
const g = {};
g['108'] = { class_type: 'UNETLoader', inputs: { unet_name: UNET, weight_dtype: 'default' } };
g['107'] = { class_type: 'VAELoader', inputs: { vae_name: 'seedvr2_ema_vae_fp16.safetensors' } };
g['1'] = { class_type: 'LoadVideo', inputs: { file: file } };
g['115'] = { class_type: 'GetVideoComponents', inputs: { video: ['1', 0] } };
g['111'] = srResizeNode(['115', 0]);
g['112'] = { class_type: 'SeedVR2Preprocess', inputs: { resized_images: ['111', 0] } };
g['106'] = { class_type: 'VAEEncodeTiled', inputs: { pixels: ['112', 0], vae: ['107', 0], tile_size: 512, overlap: 128, temporal_size: 64, temporal_overlap: 8 } };
g['114'] = { class_type: 'SeedVR2Conditioning', inputs: { model: ['108', 0], vae_conditioning: ['106', 0] } };
g['109'] = { class_type: 'KSampler', inputs: { model: ['108', 0], seed: seed, steps: 1, cfg: 1, sampler_name: 'euler', scheduler: 'simple', positive: ['114', 0], negative: ['114', 1], latent_image: ['106', 0], denoise: 1 } };
g['110'] = { class_type: 'VAEDecodeTiled', inputs: { samples: ['109', 0], vae: ['107', 0], tile_size: 512, overlap: 128, temporal_size: 64, temporal_overlap: 8 } };
g['113'] = { class_type: 'SeedVR2PostProcessing', inputs: { images: ['110', 0], original_resized_images: ['111', 0], color_correction_method: 'none' } };
g['116'] = { class_type: 'CreateVideo', inputs: { images: ['113', 0], fps: ['115', 2], audio: ['115', 1], bit_depth: ['115', 3], color_space: ['115', 4] } };
g['20'] = { class_type: 'SaveVideo', inputs: { video: ['116', 0], filename_prefix: 'canvas_sr_vid', format: 'auto', codec: 'auto' } };
""" + VIDEO_TAIL)

QW21 = (r"""// Qwen-Image 2.1（文生图 / 图像编辑 / 抠图，按模型名切换）
// quality(自动/低/中/高) 生效：映射到文本编码 resolution 与采样步数；输出尺寸取自 size。
const base = (baseUrl || '').replace(/\/+$/, '');
const p = params || {};
const isBg = /抠图/.test(model), isEdit = /编辑/.test(model);
const Q = String(p.quality || '').trim().toLowerCase();
const encRes = Q === 'high' ? 1280 : (Q === 'low' ? 768 : 1024);
const STEPS = Q === 'high' ? 40 : (Q === 'low' ? 12 : 25);
function r16(v) { return Math.max(64, Math.min(3840, Math.round(v / 16) * 16)); }
let w = 1024, h = 1024;
const szRaw = String(p.size || '');
if (/^\d+\s*[xX]\s*\d+$/.test(szRaw)) { const t = szRaw.split(/[xX]/); w = parseInt(t[0], 10); h = parseInt(t[1], 10); }
else if (/^\d+\s*:\s*\d+$/.test(szRaw)) { const t = szRaw.split(':'); const a = parseInt(t[0], 10) || 1, b = parseInt(t[1], 10) || 1; if (a >= b) { h = 1024; w = r16(1024 * a / b); } else { w = 1024; h = r16(1024 * b / a); } }
w = r16(w); h = r16(h);
""" + UPIMG + r"""
const g = {};
g['1'] = { class_type: 'UNETLoader', inputs: { unet_name: 'qwen_image_2.1_int8_convrot.safetensors', weight_dtype: 'default' } };
g['2'] = { class_type: 'CLIPLoader', inputs: { clip_name: 'qwen3vl_8b_int8_convrot.safetensors', type: 'qwen_image', device: 'default' } };
g['3'] = { class_type: 'VAELoader', inputs: { vae_name: 'qwen_image_2.1_vae_bf16.safetensors' } };
const encResEff = __imgs.length >= 3 ? Math.min(encRes, 1024) : encRes; // 参考图≥3张时 encRes=1280 触发沐曦 MACA 死锁(实测 3/4 张必挂)，1~2 张放行 1280
const encInputs = { clip: ['2', 0], vae: ['3', 0], prompt: isBg ? 'Remove the background, and output a PNG image' : String(prompt || ''), negative_prompt: String(p.negative || ''), resolution: encResEff };
for (let i = 0; i < __imgs.length && i < 9; i++) {
  const nm = await upImg(__imgs[i], 'canvas_qw21_' + i + '.png');
  const nid = String(40 + i); g[nid] = { class_type: 'LoadImage', inputs: { image: nm } };
  encInputs['images.image_' + (i + 1)] = [nid, 0];
}
g['7'] = { class_type: 'TextEncodeQwenImage21', inputs: encInputs };
let n = parseInt(p.count || '1', 10); if (!n || n < 1) n = 1; if (n > 4) n = 4;
// 有参考图(编辑)时：batch>2 会触发沐曦 MACA 采样死锁(0/12 卡死)，故改用 n 个 batch=1 分支，一次请求出 n 张
if (__imgs.length > 0) {
  for (let j = 0; j < n; j++) {
    g['lt' + j] = { class_type: 'EmptyLatentImage', inputs: { width: w, height: h, batch_size: 1 } };
    g['ks' + j] = { class_type: 'KSampler', inputs: { model: ['1', 0], seed: Math.floor(Math.random() * 1e15), steps: STEPS, cfg: 1, sampler_name: 'euler', scheduler: 'simple', positive: ['7', 0], negative: ['7', 1], latent_image: ['lt' + j, 0], denoise: 1 } };
    g['va' + j] = { class_type: 'VAEDecode', inputs: { samples: ['ks' + j, 0], vae: ['3', 0] } };
    g['sv' + j] = { class_type: 'SaveImage', inputs: { images: ['va' + j, 0], filename_prefix: 'canvas_qw21' } };
  }
} else {
  g['10'] = { class_type: 'EmptyLatentImage', inputs: { width: w, height: h, batch_size: n } };
  g['11'] = { class_type: 'KSampler', inputs: { model: ['1', 0], seed: Math.floor(Math.random() * 1e15), steps: STEPS, cfg: 1, sampler_name: 'euler', scheduler: 'simple', positive: ['7', 0], negative: ['7', 1], latent_image: ['10', 0], denoise: 1 } };
  g['12'] = { class_type: 'VAEDecode', inputs: { samples: ['11', 0], vae: ['3', 0] } };
  g['15'] = { class_type: 'SaveImage', inputs: { images: ['12', 0], filename_prefix: 'canvas_qw21' } };
}
""" + IMAGE_TAIL)

FLUX2 = (r"""// FLUX.2 参考生图（ReferenceLatent 原生参考）：支持 N 张参考图；按模型名自动 turbo/dev
// dev=20步/无LoRA；turbo=8步/+Turbo LoRA。参考图经 LoadImage→FluxKontextImageScale→VAEEncode→ReferenceLatent 注入 conditioning。
const base = (baseUrl || '').replace(/\/+$/, '');
const p = params || {};
const isTurbo = /turbo/i.test(String(model));
function r16(v) { return Math.max(64, Math.min(3840, Math.round(v / 16) * 16)); }
let w = 1024, h = 1024;
const sizeRaw = String(p.size || '');
if (/^\d+\s*[xX]\s*\d+$/.test(sizeRaw)) { const a = sizeRaw.split(/[xX]/); w = parseInt(a[0], 10); h = parseInt(a[1], 10); }
else if (/^\d+\s*:\s*\d+$/.test(sizeRaw)) { const a = sizeRaw.split(':'); const x = parseInt(a[0], 10) || 1, y = parseInt(a[1], 10) || 1; if (x >= y) { h = 1024; w = r16(1024 * x / y); } else { w = 1024; h = r16(1024 * y / x); } }
w = r16(w); h = r16(h);
let n = parseInt(p.count || '1', 10); if (!n || n < 1) n = 1; if (n > 4) n = 4;
""" + UPIMG + r"""const refs = __imgs.slice(0, 4);
const steps = isTurbo ? 8 : 20;
const seed = Math.floor(Math.random() * 4294967295);
const g = {};
g['1'] = { class_type: 'UNETLoader', inputs: { unet_name: 'flux2_dev_fp8mixed.safetensors', weight_dtype: 'default' } };
g['2'] = { class_type: 'CLIPLoader', inputs: { clip_name: 'mistral_3_small_flux2_bf16.safetensors', type: 'flux2' } };
g['3'] = { class_type: 'VAELoader', inputs: { vae_name: 'flux2-vae.safetensors' } };
g['4'] = { class_type: 'CLIPTextEncode', inputs: { text: String(prompt || ''), clip: ['2', 0] } };
g['5'] = { class_type: 'FluxGuidance', inputs: { conditioning: ['4', 0], guidance: 3.5 } };
g['6'] = { class_type: 'Flux2Scheduler', inputs: { steps: steps, width: w, height: h } };
let modelRef = ['1', 0];
if (isTurbo) { g['19'] = { class_type: 'LoraLoaderModelOnly', inputs: { model: ['1', 0], lora_name: 'Flux_2-Turbo-LoRA_comfyui.safetensors', strength_model: 1 } }; modelRef = ['19', 0]; }
let condRef = ['5', 0];
for (let i = 0; i < refs.length; i++) {
  const nm = await upImg(refs[i], 'canvas_f2_ref_' + i + '.png');
  const b = 300 + i * 4;
  g[String(b)] = { class_type: 'LoadImage', inputs: { image: nm } };
  g[String(b + 1)] = { class_type: 'FluxKontextImageScale', inputs: { image: [String(b), 0] } };
  g[String(b + 2)] = { class_type: 'VAEEncode', inputs: { pixels: [String(b + 1), 0], vae: ['3', 0] } };
  g[String(b + 3)] = { class_type: 'ReferenceLatent', inputs: { conditioning: condRef, latent: [String(b + 2), 0] } };
  condRef = [String(b + 3), 0];
}
g['9'] = { class_type: 'BasicGuider', inputs: { model: modelRef, conditioning: condRef } };
g['10'] = { class_type: 'KSamplerSelect', inputs: { sampler_name: 'euler' } };
g['11'] = { class_type: 'RandomNoise', inputs: { noise_seed: seed } };
g['7'] = { class_type: 'EmptyFlux2LatentImage', inputs: { width: w, height: h, batch_size: n } };
g['13'] = { class_type: 'SamplerCustomAdvanced', inputs: { noise: ['11', 0], guider: ['9', 0], sampler: ['10', 0], sigmas: ['6', 0], latent_image: ['7', 0] } };
g['16'] = { class_type: 'VAEDecode', inputs: { samples: ['13', 0], vae: ['3', 0] } };
g['17'] = { class_type: 'SaveImage', inputs: { filename_prefix: 'canvas_f2', images: ['16', 0] } };
""" + IMAGE_TAIL)

FLUX3 = (r"""// FLUX.3 Image Klein 文生图（抽卡）。klein=蒸馏(16步/cfg1)；klein-base=未蒸馏(50步/cfg3.5)。
// 关键：int8 注意力(comfy_kitchen sage)在沐曦 MACA 报 "CUDA driver version is insufficient"，
// 必须挂 PatchFlashAttentionKJ 强制走 flash attention（否则 base 必崩）。
// 尺寸动态传入：size(WxH 或 比例) > resolution > ratio，默认 1024x1024；r16 上限 3840。
const base = (baseUrl || '').replace(/\/+$/, '');
const p = params || {};
const isBase = /base/i.test(String(model));
const UNET = isBase ? 'flux3_image_klein_int8_convrot.safetensors' : 'flux3_image_klein_sd_int8_convrot.safetensors';
function r16(v) { return Math.max(64, Math.min(3840, Math.round(v / 16) * 16)); }
let w = 1024, h = 1024;
let sizeRaw = (p.size != null && p.size !== '') ? String(p.size) : ((p.resolution != null && p.resolution !== '') ? String(p.resolution) : ((p.ratio != null) ? String(p.ratio) : ''));
sizeRaw = sizeRaw.trim().toLowerCase().replace(/p$/, '');
if (/^\d+\s*[xX\u00d7*]\s*\d+$/.test(sizeRaw)) { const a = sizeRaw.split(/[xX\u00d7*]/); w = parseInt(a[0], 10); h = parseInt(a[1], 10); }
else if (/^\d+\s*:\s*\d+$/.test(sizeRaw)) { const a = sizeRaw.split(':'); const x = parseInt(a[0], 10) || 1, y = parseInt(a[1], 10) || 1; if (x >= y) { h = 1024; w = r16(1024 * x / y); } else { w = 1024; h = r16(1024 * y / x); } }
w = r16(w); h = r16(h);
let n = parseInt(p.count || '1', 10); if (!n || n < 1) n = 1; if (n > 4) n = 4;
let steps = isBase ? 50 : 16;
const cfg = isBase ? 3.5 : 1.0;
let clean = String(prompt || '');
const sm = /\[steps\s*[=:]\s*(\d+)\]/i.exec(clean); if (sm) { const v = parseInt(sm[1], 10); if (v > 0 && v <= 60) { steps = v; clean = clean.replace(sm[0], '').trim(); } }
const seed = Math.floor(Math.random() * 1e15);
const g = {};
g['1'] = { class_type: 'UNETLoader', inputs: { unet_name: UNET, weight_dtype: 'default' } };
g['10'] = { class_type: 'PatchFlashAttentionKJ', inputs: { model: ['1', 0], allow_compile: false } };
g['2'] = { class_type: 'CLIPLoader', inputs: { clip_name: 'qwen3vl_4b_int8_convrot.safetensors', type: 'flux3' } };
g['3'] = { class_type: 'VAELoader', inputs: { vae_name: 'flux2-vae.safetensors' } };
g['4'] = { class_type: 'CLIPTextEncode', inputs: { text: clean, clip: ['2', 0] } };
g['5'] = { class_type: 'CLIPTextEncode', inputs: { text: '', clip: ['2', 0] } };
g['6'] = { class_type: 'EmptyFlux2LatentImage', inputs: { width: w, height: h, batch_size: n } };
g['7'] = { class_type: 'KSampler', inputs: { model: ['10', 0], positive: ['4', 0], negative: ['5', 0], latent_image: ['6', 0], seed: seed, steps: steps, cfg: cfg, sampler_name: 'euler', scheduler: 'simple', denoise: 1.0 } };
g['8'] = { class_type: 'VAEDecode', inputs: { samples: ['7', 0], vae: ['3', 0] } };
g['9'] = { class_type: 'SaveImage', inputs: { images: ['8', 0], filename_prefix: 'canvas_f3' } };
""" + IMAGE_TAIL)

SD15 = r"""// SD1.5 文生图 / 图生图：有参考图则走 img2img（参考图作 latent 起点），denoise 可调（默认 0.65）
// denoise 覆盖顺序：提示词内 [denoise=0.7] > params.denoise / params.strength > 0.65
const base = (baseUrl || '').replace(/\/+$/, '');
function r16(v){ return Math.max(64, Math.min(3840, Math.round(v / 16) * 16)); }
let w = 1024, h = 1024;
const sizeRaw = (params && params.size) ? String(params.size) : '';
if (/^\d+\s*[xX]\s*\d+$/.test(sizeRaw)) {
  const p = sizeRaw.split(/[xX]/).map(function(s){ return parseInt(s.trim(), 10); });
  w = p[0]; h = p[1];
} else if (/^\d+\s*:\s*\d+$/.test(sizeRaw)) {
  const p = sizeRaw.split(':').map(function(s){ return parseInt(s.trim(), 10); });
  const a = p[0] || 1, b = p[1] || 1;
  if (a >= 64 && b >= 64) { w = a; h = b; }
  else if (a >= b) { h = 1024; w = Math.round(1024 * a / b / 16) * 16; }
  else { w = 1024; h = Math.round(1024 * b / a / 16) * 16; }
}
w = r16(w); h = r16(h);
let n = parseInt((params && params.count) || '1', 10);
if (!n || n < 1) n = 1;
if (n > 4) n = 4;
let clean = String(prompt || '');
let strength = 0.65;
if (params && params.denoise != null && /^[\d.]+$/.test(String(params.denoise))) strength = parseFloat(params.denoise);
if (params && params.strength != null && /^[\d.]+$/.test(String(params.strength))) strength = parseFloat(params.strength);
const dm = /\[denoise\s*[=:]\s*([\d.]+)\]/i.exec(clean);
if (dm) { const v = parseFloat(dm[1]); if (v > 0 && v <= 1) strength = v; clean = clean.replace(dm[0], '').trim(); }
if (!(strength > 0 && strength <= 1)) strength = 0.65;
const __imgs = (Array.isArray(images) ? images : []).filter(function (x) { return typeof x === 'string' && x.indexOf('data:image') === 0; });
const hasRef = __imgs.length > 0;
if (hasRef) n = 1;
const seed = Math.floor(Math.random() * 4294967295);
async function fitRef(src){try{var im=await new Promise(function(res,rej){var o=new Image();o.onload=function(){res(o);};o.onerror=function(){rej(new Error('x'));};o.src=src;});var ow=im.naturalWidth,oh=im.naturalHeight;if(!ow||!oh)return src;var s=1,mn=Math.min(ow,oh),mx=Math.max(ow,oh);if(mn<256)s=256/mn;if(mx*s>5760)s=Math.min(s,5760/mx);var w=Math.max(1,Math.round(ow*s)),h=Math.max(1,Math.round(oh*s)),cw=w,ch=h,ox=0,oy=0,r=w/h;if(r>2.5){ch=Math.round(w/2.5);oy=Math.round((ch-h)/2);}else if(r<0.4){cw=Math.round(h*0.4);ox=Math.round((cw-w)/2);}if(w===ow&&h===oh&&cw===ow&&ch===oh)return src;var cv=document.createElement('canvas');cv.width=cw;cv.height=ch;var cx=cv.getContext('2d');cx.fillStyle='#000';cx.fillRect(0,0,cw,ch);cx.drawImage(im,ox,oy,w,h);return cv.toDataURL('image/png');}catch(e){return src;}} async function upImg(dataUrl, name) {
  const b = await (await fetch(String(dataUrl))).blob();
  const form = new FormData();
  form.append('image', new Blob([b], { type: 'image/png' }), name);
  form.append('overwrite', 'true');
  const r = await (await fetch(base + '/upload/image', { method: 'POST', body: form })).json();
  if (!r || !r.name) throw new Error('图片上传失败: ' + JSON.stringify(r).slice(0, 150));
  return r.name;
}
const g = {};
g['1'] = { class_type: 'CheckpointLoaderSimple', inputs: { ckpt_name: 'v1-5-pruned-emaonly-fp16.safetensors' } };
g['2'] = { class_type: 'CLIPTextEncode', inputs: { text: clean, clip: ['1', 1] } };
g['3'] = { class_type: 'CLIPTextEncode', inputs: { text: params && String(params.negative || 'text, watermark'), clip: ['1', 1] } };
let latentRef = ['4', 0];
let denoise = 1;
if (hasRef) {
  const nm = await upImg(__imgs[0], 'canvas_sd15_ref.png');
  g['10'] = { class_type: 'LoadImage', inputs: { image: nm } };
  g['11'] = { class_type: 'ImageScale', inputs: { image: ['10', 0], upscale_method: 'lanczos', width: w, height: h, crop: 'center' } };
  g['12'] = { class_type: 'VAEEncode', inputs: { pixels: ['11', 0], vae: ['1', 2] } };
  latentRef = ['12', 0];
  denoise = strength;
} else {
  g['4'] = { class_type: 'EmptyLatentImage', inputs: { width: w, height: h, batch_size: n } };
}
g['5'] = { class_type: 'KSampler', inputs: { model: ['1', 0], positive: ['2', 0], negative: ['3', 0], latent_image: latentRef, seed: seed, steps: 20, cfg: 8, sampler_name: 'euler', scheduler: 'normal', denoise: denoise } };
g['6'] = { class_type: 'VAEDecode', inputs: { samples: ['5', 0], vae: ['1', 2] } };
g['7'] = { class_type: 'SaveImage', inputs: { images: ['6', 0], filename_prefix: 'canvas_sd15' } };
let sub;
try {
  const req = await fetch(base + '/prompt', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: g }) });
  sub = await req.json();
} catch (err) { throw new Error('无法连接 ComfyUI: ' + err.message); }
const pid = sub && sub.prompt_id;
if (!pid) {
  const em = (sub && sub.error && (sub.error.message || sub.error.type)) || JSON.stringify(sub).slice(0, 300);
  throw new Error('ComfyUI 提交失败: ' + em);
}
let entry = null;
const deadline = Date.now() + 15 * 60 * 1000;
while (Date.now() < deadline) {
  if (signal && signal.aborted) { (async function () { try { const q = await (await fetch(base + '/queue')).json(); const run = ((q && q.queue_running) || []).map(function (x) { return x[1]; }); if (run.indexOf(pid) >= 0) { await fetch(base + '/interrupt', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }); } else { await fetch(base + '/queue', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ delete: [pid] }) }); } } catch (e) {} })(); throw new DOMException('Aborted', 'AbortError'); }
  try {
    const hd = await (await fetch(base + '/history/' + pid)).json();
    if (hd && hd[pid]) { entry = hd[pid]; break; }
  } catch (e) {}
  await new Promise(function(r){ setTimeout(r, 4000); });
}
if (!entry) throw new Error('等待 ComfyUI 超时 (15分钟)');
const st = (entry.status && entry.status.status_str) || 'unknown';
if (st !== 'success') {
  let m = '生成失败 (' + st + ')';
  const msgs = (entry.status && entry.status.messages) || [];
  for (let i = 0; i < msgs.length; i++) {
    if (msgs[i][0] === 'execution_error' && msgs[i][1] && msgs[i][1].exception_message) { m = msgs[i][1].exception_message.slice(0, 400); break; }
  }
  throw new Error(m);
}
const outs = entry.outputs || {};
const files = [];
for (const k in outs) { if (outs[k] && outs[k].images) files.push.apply(files, outs[k].images); }
if (!files.length) throw new Error('ComfyUI 未返回图片');
function toB64(buf) {
  const bytes = new Uint8Array(buf);
  const CH = 0x8000;
  let out = '';
  for (let i = 0; i < bytes.length; i += CH) out += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
  return btoa(out);
}
const results = [];
for (let i = 0; i < files.length && i < 4; i++) {
  const f = files[i];
  const vu = base + '/view?filename=' + encodeURIComponent(f.filename) + '&subfolder=' + encodeURIComponent(f.subfolder || '') + '&type=' + encodeURIComponent(f.type || 'output');
  const ir = await fetch(vu);
  if (!ir.ok) throw new Error('获取图片失败: ' + ir.status);
  const ab = await ir.arrayBuffer();
  const ct = (ir.headers.get('Content-Type') || 'image/png').split(';')[0];
  results.push('data:' + ct + ';base64,' + toB64(ab));
}
return results;
"""

QW21T = (r"""// Qwen-Image 2.1 Viggle Turbo（v0.3 · 6 步 DMD 蒸馏 · int8 整模型）：文生图 / 图像编辑
// 官方链路：SamplerCustomAdvanced + ViggleTurboSigmas(1.0,0.9375,0.875,0.75,0.5,0.25)，BasicGuider(cfg=1)。
// quality(自动/低/中/高) 影响文本编码 resolution；输出尺寸取自 size。
const base = (baseUrl || '').replace(/\/+$/, '');
const p = params || {};
const Q = String(p.quality || '').trim().toLowerCase();
const encRes = Q === 'high' ? 1280 : (Q === 'low' ? 768 : 1024);
function r16(v) { return Math.max(64, Math.min(3840, Math.round(v / 16) * 16)); }
let w = 1024, h = 1024;
const sizeRaw = String(p.size || '');
if (/^\d+\s*[xX]\s*\d+$/.test(sizeRaw)) { const a = sizeRaw.split(/[xX]/); w = parseInt(a[0], 10); h = parseInt(a[1], 10); }
else if (/^\d+\s*:\s*\d+$/.test(sizeRaw)) { const a = sizeRaw.split(':'); const x = parseInt(a[0], 10) || 1, y = parseInt(a[1], 10) || 1; if (x >= y) { h = 1024; w = r16(1024 * x / y); } else { w = 1024; h = r16(1024 * y / x); } }
w = r16(w); h = r16(h);
""" + UPIMG + r"""
const g = {};
g['1'] = { class_type: 'UNETLoader', inputs: { unet_name: 'Qwen-Image-2.1-viggle-turbo-v0.3-6step-int8_convrot.safetensors', weight_dtype: 'default' } };
g['2'] = { class_type: 'CLIPLoader', inputs: { clip_name: 'qwen3vl_8b_int8_convrot.safetensors', type: 'qwen_image', device: 'default' } };
g['3'] = { class_type: 'VAELoader', inputs: { vae_name: 'qwen_image_2.1_vae_bf16.safetensors' } };
const encResEff = __imgs.length >= 3 ? Math.min(encRes, 1024) : encRes; // 参考图≥3张时 encRes=1280 触发沐曦 MACA 死锁(实测 3/4 张必挂)，1~2 张放行 1280
const encInputs = { clip: ['2', 0], vae: ['3', 0], prompt: String(prompt || ''), negative_prompt: '', resolution: encResEff };
for (let i = 0; i < __imgs.length && i < 9; i++) {
  const nm = await upImg(__imgs[i], 'canvas_qw21t_' + i + '.png');
  const nid = String(40 + i); g[nid] = { class_type: 'LoadImage', inputs: { image: nm } };
  encInputs['images.image_' + (i + 1)] = [nid, 0];
}
g['7'] = { class_type: 'TextEncodeQwenImage21', inputs: encInputs };
let n = parseInt(p.count || '1', 10); if (!n || n < 1) n = 1; if (n > 4) n = 4;
g['10'] = { class_type: 'EmptyLatentImage', inputs: { width: w, height: h, batch_size: n } };
g['18'] = { class_type: 'BasicGuider', inputs: { model: ['1', 0], conditioning: ['7', 0] } };
g['19'] = { class_type: 'RandomNoise', inputs: { noise_seed: Math.floor(Math.random() * 1e15) } };
g['20'] = { class_type: 'KSamplerSelect', inputs: { sampler_name: 'euler' } };
g['21'] = { class_type: 'ViggleTurboSigmas', inputs: { latent: ['10', 0], nodes: '1.0, 0.9375, 0.875, 0.75, 0.5, 0.25' } };
g['22'] = { class_type: 'SamplerCustomAdvanced', inputs: { noise: ['19', 0], guider: ['18', 0], sampler: ['20', 0], sigmas: ['21', 0], latent_image: ['10', 0] } };
g['14'] = { class_type: 'VAEDecode', inputs: { samples: ['22', 0], vae: ['3', 0] } };
g['15'] = { class_type: 'SaveImage', inputs: { images: ['14', 0], filename_prefix: 'canvas_qw21t' } };
""" + IMAGE_TAIL)

SCRIPTS = {
    "vllm": VLLM,
    "vllm_lora": VLLM_LORA,
    "sr_img": SR_IMG,
    "sr_vid": SR_VID,
    "qw21": QW21,
    "qw21t": QW21T,
    "flux2ref": FLUX2,
    "flux3": FLUX3,
    "sd15": SD15,
}

REG = r"""
window.__WFSCRIPTS = __WFSCRIPTS_JSON__;
// 同源化 + 每用户 token：从本页 URL 的 ?token= 取 token，拼成同源路径
window.__IC_TQ = '';
try { window.__IC_TQ = (new URLSearchParams(location.search).get('token') || '').trim(); } catch (e) {}
window.__IC_IMGURL = '/img' + (window.__IC_TQ ? '/' + window.__IC_TQ : '');
window.__IC_H3URL  = '/h3'  + (window.__IC_TQ ? '/' + window.__IC_TQ : '');
window.runWorkflowsImport = function () {
  var KEY = "infinite-canvas:ai_config_store";
  var cur = JSON.parse(localStorage.getItem(KEY) || "{}");
  cur.state = cur.state || {}; cur.state.config = cur.state.config || {};
  var chans = cur.state.config.channels = cur.state.config.channels || [];
  // 同源化 + 每用户 token（全局定义见本脚本顶部的 __IC_*）
  var IMGURL = window.__IC_IMGURL, H3URL = window.__IC_H3URL;
  function getCh(id, name, url) {
    var c = null;
    for (var i = 0; i < chans.length; i++) { if (chans[i] && (chans[i].id === id || chans[i].name === name)) { c = chans[i]; break; } }
    if (!c) { c = { id: id, name: name, baseUrl: url, apiKey: "comfyui-local", apiFormat: "openai", models: [] }; chans.push(c); }
    c.baseUrl = url; c.apiKey = "comfyui-local"; c.apiFormat = "openai";
    c.models = c.models || [];
    return c;
  }
  function upsert(ch, name, cap, script) {
    for (var i = 0; i < ch.models.length; i++) { if (ch.models[i] && ch.models[i].name === name) { ch.models[i].capability = cap; ch.models[i].script = script; return; } }
    ch.models.push({ name: name, capability: cap, script: script });
  }
  // 1) 把历史绝对地址统一改写为同源路径（图片→/img/<token>，视频→/h3/<token>）
  for (var j = 0; j < chans.length; j++) {
    var cc = chans[j];
    if (!cc || typeof cc.baseUrl !== "string") continue;
    if (cc.baseUrl.indexOf(":18188") >= 0) cc.baseUrl = H3URL;
    else if (cc.baseUrl.indexOf(":18422") >= 0 || cc.baseUrl.indexOf(":18421") >= 0) cc.baseUrl = IMGURL;
  }
  var S = window.__WFSCRIPTS;
  // 2) H3 渠道：追加 vllm 视频 + SeedVR2 超分
  var H3 = getCh("1GyO55Q-dNU_-OIOfcSB_", "海螺H3-ComfyUI", H3URL);
  // 清理历史遗留：文生(t2va)+vllm LoRA 曾出噪声（服务端缺陷，已由 e4f046e3 + #7047/#7219 修复）—— 现恢复注册
  upsert(H3, "H3文生视频·vllm版", "video", S.vllm);
  upsert(H3, "H3图生视频·vllm版", "video", S.vllm);
  upsert(H3, "H3参考生视频·vllm版", "video", S.vllm); upsert(H3, "H3参考生视频·vllm版·省流", "video", S.vllm);
  // 2b) H3 渠道：追加 vllm LoRA 加速版（挂官方 4 步 LoRA）
  // 文生/图生/参考生均可用（t2va 复用 fl2v turbo LoRA；2026-10-15 实测清洁）
  upsert(H3, "H3文生视频·vllm版·LoRA加速", "video", S.vllm_lora);
  upsert(H3, "H3图生视频·vllm版·LoRA加速", "video", S.vllm_lora);
  upsert(H3, "H3参考生视频·vllm版·LoRA加速", "video", S.vllm_lora); upsert(H3, "H3参考生视频·vllm版·LoRA加速·省流", "video", S.vllm_lora);
  // BSA 版：同一脚本，只有名称带 BSA 的渠道才打开块稀疏（默认关闭）
  upsert(H3, "H3文生视频·vllm版·LoRA加速·BSA", "video", S.vllm_lora);
  upsert(H3, "H3图生视频·vllm版·LoRA加速·BSA", "video", S.vllm_lora);
  upsert(H3, "H3参考生视频·vllm版·LoRA加速·BSA", "video", S.vllm_lora); upsert(H3, "H3参考生视频·vllm版·LoRA加速·省流·BSA", "video", S.vllm_lora);
  upsert(H3, "SeedVR2图片超分·3B", "image", S.sr_img);
  upsert(H3, "SeedVR2图片超分·7B", "image", S.sr_img);
  upsert(H3, "SeedVR2视频超分·3B", "video", S.sr_vid);
  upsert(H3, "SeedVR2视频超分·7B", "video", S.sr_vid);
  // 3) 图像渠道：Qwen-Image 2.1
  var Q = getCh("comfyui-qwen21", "ComfyUI Qwen-Image 2.1", IMGURL);
  upsert(Q, "qwen21 文生图", "image", S.qw21);
  upsert(Q, "qwen21 图像编辑", "image", S.qw21);
  upsert(Q, "qwen21 抠图", "image", S.qw21);
  // 3b) 覆盖 FLUX.2 渠道脚本：加参考图强度（否则参考图等同无效）
  var F2 = getCh("comfyui-f2", "ComfyUI FLUX.2", IMGURL);
  upsert(F2, "flux2-dev", "image", S.flux2ref);
  upsert(F2, "flux2-dev-turbo", "image", S.flux2ref);
  // 3c) SD1.5：补 img2img（有参考图时用参考图作 latent 起点，denoise 可调）
  var SD = getCh("comfyui-sd15", "ComfyUI SD1.5", IMGURL);
  upsert(SD, "sd15", "image", S.sd15);
  // 3d) Qwen-Image 2.1 Viggle Turbo（v0.3 · 6 步 DMD 蒸馏 · int8 整模型）
  var QT = getCh("comfyui-qwen21t", "ComfyUI Qwen-Image 2.1 Turbo", IMGURL);
  upsert(QT, "qwen21-turbo 文生图", "image", S.qw21t);
  upsert(QT, "qwen21-turbo 图像编辑", "image", S.qw21t);
  // 3e) FLUX.3 Image Klein（klein=蒸馏 16步/cfg1；klein-base=未蒸馏 50步/cfg3.5）
  var F3 = getCh("comfyui-f3", "ComfyUI FLUX.3", IMGURL);
  upsert(F3, "flux3-klein", "image", S.flux3);
  upsert(F3, "flux3-klein-base", "image", S.flux3);
  // 4) 重建模型引用索引
  var ourIds = {}; ourIds[H3.id] = 1; ourIds[Q.id] = 1; ourIds[QT.id] = 1; ourIds[F3.id] = 1;
  cur.state.config.models = cur.state.config.models || [];
  cur.state.config.models = cur.state.config.models.filter(function (m) {
    if (typeof m !== "string") return true;
    return !(m.indexOf(H3.id + "::") === 0 || m.indexOf(Q.id + "::") === 0 || m.indexOf(QT.id + "::") === 0 || m.indexOf(F3.id + "::") === 0);
  });
  [H3, Q, QT, F3].forEach(function (c) { c.models.forEach(function (m) { cur.state.config.models.push(c.id + "::" + m.name); }); });
  if (!cur.state.config.videoModel) cur.state.config.videoModel = H3.id + "::" + H3.models[1].name;
  if (window.__cfgDualWrite) window.__cfgDualWrite(cur); else localStorage.setItem(KEY, JSON.stringify(cur));
  return { h3: H3.models.length, qw21: Q.models.length, qw21t: QT.models.length };
};
// 兜底归一化：任何导入动作后，把所有渠道地址统一为同源（覆盖 __IMG 里的历史 7 个绘图渠道）
window.__normalizeChannels = function () {
  var KEY = "infinite-canvas:ai_config_store";
  var cur; try { cur = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return; }
  var chans = (cur.state && cur.state.config && cur.state.config.channels) || [];
  var changed = false;
  for (var i = 0; i < chans.length; i++) {
    var cc = chans[i]; if (!cc || typeof cc.baseUrl !== "string") continue;
    var ob = cc.baseUrl;
    if (ob.indexOf(":18188") >= 0) cc.baseUrl = window.__IC_H3URL;
    else if (ob.indexOf(":18422") >= 0 || ob.indexOf(":18421") >= 0) cc.baseUrl = window.__IC_IMGURL;
    if (cc.baseUrl !== ob) changed = true;
  }
  if (changed) { if (window.__cfgDualWrite) window.__cfgDualWrite(cur); else localStorage.setItem(KEY, JSON.stringify(cur)); }
};
(function () {
  function wrap(fnName, after) {
    var orig = window[fnName];
    if (typeof orig === "function" && !orig.__wfWrapped) {
      var w = function () { var r = orig.apply(this, arguments); try { after(); } catch (e) { console.error(fnName, e); } return r; };
      w.__wfWrapped = true; window[fnName] = w;
    }
  }
  wrap("runExtraImport", function () { window.runWorkflowsImport(); window.__normalizeChannels(); });
  wrap("runImageChannelsImport", function () { window.__normalizeChannels(); });
})();
"""

NEW_BTN = "一键初始化（全部工作流：H3 视频含 vLLM LoRA 加速 + 超分 + 图像渠道含 Qwen-Image 2.1）"
OLD_BTN = "一键初始化（7 个视频模型 + 7 个画图渠道 + 4 个 GPT 系模型 + 2 个插件）"

html = open(SRC, encoding="utf-8").read()
reg = REG.replace("__WFSCRIPTS_JSON__", json.dumps(SCRIPTS, ensure_ascii=False))
block = "\n<script>\n" + reg + "\n</script>\n"
assert "</body>" in html, "no </body>"
html = html.replace("</body>", block + "</body>", 1)
# relabel main button
if OLD_BTN in html:
    html = html.replace(OLD_BTN, NEW_BTN, 1)
else:
    print("WARN: old button text not found")
# 修正 H3 脚本双实例分流的浏览器侧目标端口：18421(仅宿主机内可达) -> 18422(对外 CORS 代理)
SPILL_OLD = '\\":18188\\", \\":18421\\"'
SPILL_NEW = '\\":18188\\", \\":18422\\"'
spill_n = html.count(SPILL_OLD)
html = html.replace(SPILL_OLD, SPILL_NEW)
print("spillover port fixed:", spill_n)
assert spill_n > 0, "spillover pattern not found"
# 同源化：页面内联脚本注册 H3 渠道用的 __BASE 也改为同源 /h3（带 ?token=）
BASE_OLD = 'const __BASE = "http://140.207.205.59:18188";'
BASE_NEW = 'const __BASE = (function(){try{var q=(new URLSearchParams(location.search).get("token")||"").trim();return "/h3"+(q?"/"+q:"");}catch(e){return "/h3";}})();'
base_n = html.count(BASE_OLD)
html = html.replace(BASE_OLD, BASE_NEW)
print("__BASE same-origin rewrite:", base_n)
assert base_n > 0, "__BASE pattern not found"
NOTE = ('<div style="background:#0d1117;border:1px solid #238636;border-radius:8px;padding:10px 12px;margin:10px 0;font-size:13px;line-height:1.7">'
        '本页在原有基础上<b>追加注册</b>：H3 文生/图生/参考生视频·<b>vllm版</b>（3）、H3 <b>文生/图生/参考生视频·vllm版·LoRA加速</b>（3，挂官方 4 步 LoRA，num_inference_steps=4）、<b>SeedVR2 图片超分·3B/7B</b>（2，图片）、'
        '<b>SeedVR2 视频超分·3B/7B</b>（2）、<b>Qwen-Image 2.1 文生图/图像编辑/抠图</b>（3，图像渠道）；'
        '并把图像渠道端口统一为对外可达的 CORS 代理 <b>18422</b>；修正 H3 双实例分流的浏览器侧目标端口 <b>18421→18422</b>；'
        '修复 <b>qwen21 参考不生效</b>（补 TEQ21 的 <code>vae</code> + KSampler 改用参考 LATENT）与 <b>FLUX.2 参考失效</b>（改为 <code>ReferenceLatent</code> 原生参考注入，支持多参考图）；为 <b>SD1.5</b> 补上 <code>img2img</code>（参考图作 latent 起点，<code>denoise</code> 可调，默认 0.65）；'
        '新增 <b>Qwen-Image 2.1 Viggle Turbo</b> 渠道（v0.3 · 6 步 DMD 蒸馏 int8 整模型，<code>SamplerCustomAdvanced</code> + <code>ViggleTurboSigmas</code>）；'
        '让 <b>qwen21 的 quality 生效</b>（低/中/高 → 文本编码分辨率 768/1024/1280 与步数 12/25/40，输出尺寸仍取自 size）；'
        '修复 <b>r16 上限 2048 导致 4K 被压成 1:1</b>（上限提到 3840，qwen21/FLUX.2/SD1.5 同步）。</div>')
if '<p class="sub">' in html:
    html = html.replace('<p class="sub">', NOTE + '<p class="sub">', 1)
else:
    print("WARN: sub paragraph not found")

# --- 同步覆盖 __IMG 中 comfyui-f2（flux2-dev / flux2-dev-turbo）的脚本为新的 FLUX2 ---
def _str_between(t, q):
    i = q + 1
    parts = []
    while i < len(t):
        c = t[i]
        if c == "\\":
            parts.append(t[i:i + 2]); i += 2; continue
        if c == '"':
            return i + 1, "".join(parts)
        parts.append(c); i += 1
    raise ValueError("unterminated string")

_lb = html.find("const __IMG")
_lb = html.find("[", _lb)
_new_enc = json.dumps(FLUX2, ensure_ascii=True)[1:-1]
for _mn in ["flux2-dev-turbo", "flux2-dev"]:
    _k = html.find('"name": "%s"' % _mn, _lb)
    _sk = html.find('"script": "', _k)
    _q = _sk + len('"script": ')
    _end, _raw = _str_between(html, _q)
    html = html.replace(html[_q:_end], '"' + _new_enc + '"', 1)
    print("__IMG patched:", _mn)

_sd15_enc = json.dumps(SD15, ensure_ascii=True)[1:-1]
_k = html.find('"name": "sd15"', _lb)
_sk = html.find('"script": "', _k)
_q = _sk + len('"script": ')
_end, _raw = _str_between(html, _q)
html = html.replace(html[_q:_end], '"' + _sd15_enc + '"', 1)
print("__IMG patched: sd15")

# 单卡化兜底：把残留的 flux2 MultiGPU loader（如 image_fx2 渠道）统一换回标准 loader，
# 使 workflow 在「单卡 worker + CUDA_VISIBLE_DEVICES 钉卡」下正确落卡（而非写死物理卡）。
html = html.replace(
    "{ class_type: 'UNETLoaderMultiGPU', inputs: { unet_name: 'flux2_dev_fp8mixed.safetensors', weight_dtype: 'default', device: 'cuda:1' } }",
    "{ class_type: 'UNETLoader', inputs: { unet_name: 'flux2_dev_fp8mixed.safetensors', weight_dtype: 'default' } }")
html = html.replace(
    "{ class_type: 'CLIPLoaderMultiGPU', inputs: { clip_name: 'mistral_3_small_flux2_bf16.safetensors', type: 'flux2', device: 'cuda:1' } }",
    "{ class_type: 'CLIPLoader', inputs: { clip_name: 'mistral_3_small_flux2_bf16.safetensors', type: 'flux2' } }")
html = html.replace(
    "{ class_type: 'VAELoaderMultiGPU', inputs: { vae_name: 'flux2-vae.safetensors', device: 'cuda:1' } }",
    "{ class_type: 'VAELoader', inputs: { vae_name: 'flux2-vae.safetensors' } }")
print("flux2 single-card normalize done")

open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT, len(html), "bytes")
print("scripts:", {k: len(v) for k, v in SCRIPTS.items()})
