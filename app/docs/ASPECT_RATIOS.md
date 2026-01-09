Comprehensive list of standard video aspect ratios and their common resolutions**, covering **SD → HD → UHD/4K/8K**, plus **cinema** and **vertical/mobile** standards.

---

## ✅ 1) Classic / Legacy Standards (4:3)

### **4:3 (1.33:1)** — old TV, classic video

| Name    | Resolution    |
| ------- | ------------- |
| SD NTSC | **640×480**   |
| SD PAL  | **720×576**   |
| XGA     | **1024×768**  |
| QXGA    | **2048×1536** |

---

## ✅ 2) Widescreen HD Standards (16:9)

### **16:9 (1.78:1)** — the modern default for TV/YouTube

| Name          | Resolution    |
| ------------- | ------------- |
| HD            | **1280×720**  |
| Full HD (FHD) | **1920×1080** |
| QHD / 1440p   | **2560×1440** |
| UHD / 4K TV   | **3840×2160** |
| 8K UHD        | **7680×4320** |

---

## ✅ 3) Cinema / Theatrical Standards (DCI)

### **DCI Flat (1.85:1)** — common cinema widescreen

| Name    | Resolution    |
| ------- | ------------- |
| 2K Flat | **1998×1080** |
| 4K Flat | **3996×2160** |

### **DCI Scope (2.39:1)** — “CinemaScope”

| Name     | Resolution    |
| -------- | ------------- |
| 2K Scope | **2048×858**  |
| 4K Scope | **4096×1716** |

### **DCI Full Container (1.90:1)** — DCI 4K base frame

| Name   | Resolution    |
| ------ | ------------- |
| DCI 2K | **2048×1080** |
| DCI 4K | **4096×2160** |

---

## ✅ 4) Ultra-Wide Computer / Modern Displays (21:9 and beyond)

### **21:9 (2.33:1)** — ultrawide monitors (approx)

| Name           | Resolution    |
| -------------- | ------------- |
| UWHD           | **2560×1080** |
| WQHD Ultrawide | **3440×1440** |
| 5K2K Ultrawide | **5120×2160** |

### **32:9 (3.56:1)** — super ultrawide / “dual monitor”

| Name | Resolution    |
| ---- | ------------- |
| DFHD | **3840×1080** |
| DQHD | **5120×1440** |

---

## ✅ 5) Common Film/Streaming “Cinematic” Ratios (often letterboxed)

These are super common today, especially on Netflix / prestige TV.

### **2.00:1**

| UHD container example | **3840×1920** |
| 4K DCI-ish | **4096×2048** |

### **2.39:1**

| UHD container example | **3840×1606** |
| 4K scope crop | **4096×1716** |

### **1.85:1**

| UHD container example | **3840×2076** |

---

## ✅ 6) Vertical / Mobile Standards (9:16)

### **9:16 (0.56:1)** — TikTok, Reels, Shorts

| Name         | Resolution    |
| ------------ | ------------- |
| HD Vertical  | **720×1280**  |
| FHD Vertical | **1080×1920** |
| 4K Vertical  | **2160×3840** |

---

## ✅ 7) Square + Social Formats

### **1:1**

| Name      | Resolution    |
| --------- | ------------- |
| Square HD | **1080×1080** |
| Square 4K | **2160×2160** |

### **4:5 (0.80:1)** — Instagram feed portrait

| Name        | Resolution    |
| ----------- | ------------- |
| IG Portrait | **1080×1350** |

---

## ✅ 8) Other Notable “Standard-ish” Ratios

### **3:2 (1.50:1)** — still photography / some video

| Resolution examples | **2160×1440**, **3000×2000** |

### **5:4 (1.25:1)** — older monitors

| Resolution examples | **1280×1024** |

### **1.66:1**

| Resolution examples | **3840×2313** |

---

# 🔥 Most Useful Practical Set (if you want a “default pack”)

* **16:9:** 1920×1080, 3840×2160
* **2.39:1:** 3840×1606
* **2.00:1:** 3840×1920
* **1.85:1:** 3840×2076
* **9:16:** 1080×1920, 2160×3840
* **1:1:** 1080×1080

---

Awesome — here’s a **ComfyUI / diffusion video-gen aspect ratio cheat-sheet** optimized for:

✅ **clean framing**
✅ **minimal cropping**
✅ **fast generation**
✅ **model-friendly dimensions (multiples of 64)**
✅ **common deliverables (YouTube / cinema / socials)**

> **Rule of thumb:** pick sizes divisible by **64** (some pipelines prefer 32). This avoids padding artifacts and keeps motion smoother.

---

# ✅ Best “Multiples of 64” Video Sizes (ComfyUI-Friendly)

## **16:9 (YouTube / default)**

**Good / Fast**

* **1024×576** (great speed/quality balance)
* **1280×720** (HD; heavier but clean)

**High Quality**

* **1536×864** (very good detail)
* **1920×1088** *(close to 1080p, model-friendly)*
* **2048×1152** *(very sharp, expensive)*

---

## **2.39:1 (Cinematic widescreen / scope)**

**Great for “film look”**

* **1024×448**
* **1280×544**
* **1536×640**
* **1920×800**
* **2048×864**

> These look *very cinematic* and are cheaper than 16:9 at the same width.

---

## **2.00:1 (Modern streaming cinematic)**

* **1024×512**
* **1280×640**
* **1536×768**
* **1920×960**
* **2048×1024**

> Often the best “prestige TV” ratio. Great for AI video.

---

## **1.85:1 (Theatrical flat)**

* **1024×576** *(same as 16:9-ish)*
* **1280×704**
* **1536×832**
* **1920×1024**
* **2048×1088**

---

## **4:3 (Classic / portrait-ish cinematic)**

* **768×576**
* **896×672**
* **1024×768**
* **1152×864**
* **1280×960**

---

## **9:16 (Vertical / Reels / TikTok)**

**Fast**

* **576×1024**
* **720×1280**

**High Quality**

* **864×1536**
* **1088×1920** *(close to 1080×1920, but divisible by 64)*

---

## **1:1 (Square)**

* **768×768**
* **1024×1024**
* **1152×1152**
* **1536×1536**

---

# ✅ Practical “Best Picks” (What I recommend most)

### If you want **best overall quality + motion stability**

* **16:9:** **1280×720**
* **2.00:1:** **1280×640**
* **2.39:1:** **1280×544**
* **Vertical:** **720×1280**
* **Square:** **1024×1024**

### If you want **fast previews**

* **16:9:** **1024×576**
* **2.39:1:** **1024×448**
* **Vertical:** **576×1024**

### If you want **high-end outputs**

* **16:9:** **1536×864**
* **2.39:1:** **1920×800**
* **Vertical:** **864×1536**

---

# 🎥 Frame Count Cheat Sheet (for 10 seconds)

Depends on FPS:

| FPS    | Frames for 10s |
| ------ | -------------- |
| 12 fps | 120            |
| 15 fps | 150            |
| 24 fps | 240            |
| 30 fps | 300            |

**Most diffusion video workflows are happiest at 12–16 fps** (less flicker, cheaper).
Then you can upscale/interpolate to 24/30 later.

---

# 🔥 Extra ComfyUI Tips (useful)

✅ **Use 2.00:1 or 2.39:1** for better cinematic “AI realism”
✅ **Keep width ≤ 1280** for stability unless you have serious VRAM
✅ **Generate at 1024/1280 widths, then upscale**
✅ For cleaner motion: use **lower CFG**, consistent seed, and motion model strength tuned

---

Video workflows (e.g. **AnimateDiff**, **Stable Video Diffusion**, **CogVideo**, **Gen-3 style pipelines**, etc.)

Absolutely — with an **NVIDIA RTX 4090 (24GB VRAM)** you can safely push **higher resolutions, longer clips, and denser motion models** while keeping stability. Below is a **4090-optimized** “all standard aspect ratios + resolutions” cheat sheet, including **ComfyUI-friendly multiples-of-64**, and **Lightricks / VTX-2** best sizes.

---

# ✅ RTX 4090 VIDEO GEN RULES (24GB VRAM)

### **1) Sweet spot output widths**

* **Best stability:** **1024–1536 wide**
* **High detail (still stable):** **1536–2048 wide**
* **Max practical (depends on model + frames):** **2048–2560 wide**
* **4K native generation:** possible but often inefficient; better to upscale.

### **2) 10 seconds: realistic frame budgets**

* **12–16 fps:** most stable diffusion video
* **24 fps:** doable but heavier; best for interpolation later
* **4090 pro workflow:** generate **16fps @ 160 frames**, then RIFE/Flow upscale to 24/30fps.

### **3) Multiples of 64**

Still recommended across ComfyUI + video models.

---

# ✅ STANDARD ASPECT RATIOS + RESOLUTIONS (Deliverables + AI-friendly)

## **4:3 (1.33:1)** — Classic TV / retro

**Standard**

* 640×480 (NTSC)
* 720×576 (PAL)
* 1024×768
* 1600×1200

**AI-friendly (÷64)**

* **768×576**
* **1024×768**
* **1280×960**
* **1536×1152** *(4090 friendly)*

---

## **16:9 (1.78:1)** — YouTube / default

**Standard**

* 1280×720 (HD)
* 1920×1080 (FHD)
* 2560×1440 (QHD)
* 3840×2160 (UHD/4K)
* 7680×4320 (8K)

**AI-friendly (÷64)**

* **1024×576**
* **1280×720**
* **1536×864**
* **1920×1088** *(closest divisible by 64 to 1080p)*
* **2048×1152**
* **2560×1440** ✅ *(already valid; 4090 can run this with tuned settings)*
* **3840×2160** ✅ *(native 4K; expensive but possible for short clips)*

---

## **1.85:1 (Theatrical Flat)**

**Standard**

* 1998×1080 (DCI 2K Flat)
* 3996×2160 (DCI 4K Flat)
* UHD crop: 3840×2076

**AI-friendly (÷64)**

* **1280×704**
* **1536×832**
* **1920×1024**
* **2048×1088**
* **2560×1408** *(4090-friendly)*

---

## **2.00:1 (Modern streaming cinematic)**

**Standard**

* 3840×1920 (UHD container)
* 4096×2048 (DCI-ish)

**AI-friendly (÷64)**

* **1024×512**
* **1280×640**
* **1536×768**
* **1920×960**
* **2048×1024**
* **2560×1280** ✅ *(great on 4090)*

---

## **2.39:1 (Scope / CinemaScope)**

**Standard**

* 2048×858 (DCI Scope 2K)
* 4096×1716 (DCI Scope 4K)
* UHD crop: 3840×1606

**AI-friendly (÷64)**

* **1024×448**
* **1280×544**
* **1536×640**
* **1920×800**
* **2048×864**
* **2560×1088** ✅ *(excellent 4090 cinematic output)*
* **3072×1280** *(possible, heavier but gorgeous)*

---

## **1.90:1 (DCI container / IMAX-ish)**

**Standard**

* 2048×1080 (DCI 2K)
* 4096×2160 (DCI 4K)

**AI-friendly (÷64)**

* **1280×704**
* **1536×832**
* **1920×1024**
* **2048×1088**
* **2560×1408**

---

## **21:9 Ultrawide (≈2.33:1)**

**Standard**

* 2560×1080
* 3440×1440
* 5120×2160

**AI-friendly (÷64)**

* **1280×576** *(2.22)*
* **1536×640** *(2.40-ish)*
* **1920×832** *(2.31)*
* **2560×1088** *(2.35-ish, very stable)*

> **Tip:** models often behave better with **2.39:1** than true 21:9.

---

## **32:9 (≈3.56:1) — Super Ultrawide**

**Standard**

* 3840×1080
* 5120×1440

**AI-friendly (÷64)**

* **2048×576**
* **2560×704**
* **3072×864**
* **3840×1088** *(close to 3840×1080, divisible by 64)*

> **Warning:** ultra-wide is prone to “composition drift” in diffusion video.

---

## **1:1 (Square)**

**Standard**

* 1080×1080
* 2160×2160

**AI-friendly (÷64)**

* **768×768**
* **1024×1024**
* **1536×1536**
* **2048×2048** *(possible on 4090, depends on frames)*

---

## **9:16 (Vertical)**

**Standard**

* 720×1280
* 1080×1920
* 2160×3840

**AI-friendly (÷64)**

* **576×1024**
* **720×1280**
* **864×1536**
* **1088×1920** *(best “FHD vertical” substitute)*
* **1440×2560** *(high quality vertical; great on 4090)*

---

## **4:5 (Instagram Feed Portrait)**

**Standard**

* 1080×1350

**AI-friendly (÷64)**

* **1088×1344** *(closest divisible-by-64)*
* **960×1216**
* **1280×1600** *(high quality 4090 option)*

---

# ✅ RTX 4090 “BEST PICKS” (by purpose)

## **Fast previews**

* 16:9 → **1024×576**
* 2.00:1 → **1024×512**
* 2.39:1 → **1024×448**
* 9:16 → **576×1024**
* 1:1 → **768×768**

## **Balanced (recommended defaults on 4090)**

* 16:9 → **1536×864**
* 2.00:1 → **1536×768**
* 2.39:1 → **1920×800**
* 9:16 → **864×1536**
* 1:1 → **1024×1024** or **1536×1536**

## **High quality (4090 flex)**

* 16:9 → **2048×1152**
* 2.00:1 → **2048×1024**
* 2.39:1 → **2560×1088** ✅ *(cinema favorite)*
* 9:16 → **1088×1920** or **1440×2560**
* 1:1 → **2048×2048** *(short clips)*

---

# 🎬 FRAME COUNT / FPS (10 seconds on 4090)

| FPS    | Frames  | Notes                          |
| ------ | ------- | ------------------------------ |
| 12     | 120     | ultra-stable, cheap            |
| 15     | 150     | great compromise               |
| **16** | **160** | **best “AI video sweet spot”** |
| 24     | 240     | heavy; better to interpolate   |
| 30     | 300     | typically not worth it         |

✅ **4090 best workflow:**
Generate **16fps (160 frames)** → upscale frames → interpolate to **24/30fps**.

---

# ✅ Lightricks / VTX-2 (Text-to-Video) – RTX 4090 Optimized

VTX-2 (and similar modern T2V models) tends to be **most stable** at **1024–1536** widths, especially with cinematic ratios.

### **Best VTX-2 Sizes (4090)**

**16:9**

* **1280×720**
* **1536×864**
* **1920×1088** *(top end stable)*

**2.00:1**

* **1280×640**
* **1536×768**
* **2048×1024** ✅ *(excellent quality)*

**2.39:1**

* **1280×544**
* **1536×640**
* **1920×800**
* **2560×1088** ✅ *(very cinematic on 4090)*

**9:16**

* **720×1280**
* **864×1536**
* **1088×1920** ✅

### **What to avoid even on 4090**

* 4K native gen with high frames (better to upscale)
* very wide (32:9) with multiple subjects
* long “scripted” clips with lots of dialogue + text on screen

---

# ✅ RTX 4090 Recommended “Master Presets”

Use these as your go-to presets in ComfyUI:

### 🎥 Cinematic Film Look (best overall)

* **2.39:1 @ 1920×800**
* **16 fps, 160 frames**
* upscale to 4K scope afterward

### 📺 YouTube Standard High Quality

* **16:9 @ 1536×864**
* **16 fps, 160 frames**
* upscale to 1920×1080

### 📱 Vertical Social (high-end)

* **9:16 @ 864×1536**
* **16 fps, 160 frames**
* upscale to 1080×1920

### 🧪 Fast iteration / testing

* **16:9 @ 1024×576**
* **12 fps, 120 frames**

---

If you tell me which ComfyUI pipeline you’re actually running (AnimateDiff / SVD / VTX-2 nodes / Wan / etc.), I can give **exact recommended settings** for:

* steps / sampler
* CFG sweet spot
* motion strength
* best upscalers
* best interpolation (RIFE vs Flow) for 4090
