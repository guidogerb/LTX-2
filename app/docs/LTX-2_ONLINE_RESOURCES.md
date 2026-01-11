The most useful how‑to material on LTX‑2 right now clusters into four groups: official docs, ComfyUI pipeline guides (including the three repos you cited), third‑party deep‑dives, and hands‑on video tutorials.[1][2][3][4][5][6][7][8][9][10]

Below is a curated list, with notes about what each source covers and how it relates to the ComfyUI‑LTXVideo vs. your LTX‑2 pipelines vs. the ltx.io guide.

## Official LTX‑2 documentation

- LTX-2: Production-Grade AI Video Generation Model – Model overview, capabilities (4K, FPS, long‑form), and links out to docs, examples, and roadmap.[10]
- Prompting Guide | LTX Documentation – Core, model‑agnostic LTX‑2 prompt structure: scene → action → characters → camera → audio; emphasizes single flowing paragraph, present‑tense action and concrete physical cues.[8]  
- Lightricks/LTX-2 (official Python inference & LoRA trainer) – Shows the canonical Python pipelines (text‑to‑AV, image‑to‑AV), describes `enhance_prompt`, and gives a clean reference for model inputs/outputs and shot‑style prompting.[5]
- LTX-2 API Prompting Guide on ltx.video (linked from the repo) – Extended prompting article referenced in the README; elaborates on best practices and common failure modes when moving from short clips to near‑max‑length shots.[5]

These are the “ground truth” for how the model behaves and are the best baseline when comparing any custom ComfyUI or custom‑Python pipeline choices (samplers, latent scale, audio options, etc.).[8][10][5]

## ComfyUI pipelines and differences

- Lightricks/ComfyUI-LTXVideo – Reference ComfyUI node pack for LTX‑Video / LTX‑2.  
  - Provides simplified flows (image‑to‑video, image‑to‑video with keyframes, etc.) and is tightly aligned with the official LTX‑2 repo in terms of scheduler choices and prompt usage.[2][1]
  - The example workflows here show the “intended” node graph: where conditioning, keyframes, and IC‑LoRA go, and how audio is toggled or routed.[1][2]

- GuidoGerbPublishing/LTX-2 – Your custom pipeline repo.  
  - From the snippet and structure, this repo diverges mainly in workflow ergonomics: more opinionated defaults, custom compositing/utility nodes, and specific presets for creative shot types (e.g., cinematic, music‑video‑style, etc.) rather than the minimal reference flows in ComfyUI‑LTXVideo.[11]
  - Where ComfyUI‑LTXVideo hews closely to the official LTX‑2 configs, this repo is better viewed as a “creative workstation” pipeline: the same core model, but different pre‑ and post‑processing and likely different defaults for motion strength, seed reuse, and chaining clips.[11][2][1]

- ComfyUI Wiki – LTX Video Workflow Step-by-Step Guide – Long‑form article that walks through installing LTXVideo nodes, loading models, and building a full graph for i2v and t2v.[3]
  - Clarifies what each ComfyUI‑LTXVideo node is doing (latent setup, motion parameters, decoding), which helps when mapping those nodes to the Python pipelines in the official LTX‑2 repo or to custom variations in your own repo.[2][3][1]

- ComfyUI-LTXTricks on RunComfy – Advanced ComfyUI extension for LTX models (RF‑Inversion, RF‑Edit, FlowEdit, enhanced sampling, interpolation, tighter per‑frame control).[12][2]
  - Pairs well with both ComfyUI‑LTXVideo and your LTX‑2 graphs as an “advanced layer” for editing, re‑timing, and interpolating clips without leaving ComfyUI.[12][2]

In practice:  
- ComfyUI‑LTXVideo ≈ canonical node representation of official LTX‑2 pipelines.  
- GuidoGerbPublishing/LTX‑2 ≈ opinionated, production‑oriented graphs tuned for creative workflows and clip chaining.  
- LTX docs/site ≈ model behavior and prompting semantics independent of UI.[8][10][1][2][5]

## Prompting & creative usage (text, camera, audio)

- Prompting Guide for LTX-2 | Ltx-2 – The official blog‑style prompting guide from ltx.io (your original link).  
  - Focuses on *creative* structuring of prompts: shot language, motion verbs, camera‑relative phrasing, and how to articulate multi‑beat actions without confusing temporal ordering.[10]

- LTX-2 Prompting Guide: Master AI Video Generation with Expert Techniques (dev.to) – Deep dive into six essential elements of LTX‑2 prompts: subject, action, camera/lens, visual style, narrative flow, and audio sync.[4]
  - Discusses different strategies for short vs. long shots and gives explicit examples of “mini‑scene” prompts for near‑20‑second clips, which map directly onto both the official Python pipelines and ComfyUI graphs.[4][5]

- LTX-2 Prompting section in Lightricks/LTX-2 README – Compact, strongly opinionated rules: single paragraph, detailed chronological description, concrete camera and movement specification, within ~200 words.[5]
  - This is the tightest statement of what the underlying DiT expects; it’s particularly useful when debugging pipeline differences because it isolates prompt issues from graph differences.[5]

- Prompting Guide | LTX-2 API docs – API‑oriented but still highly relevant for creative users; emphasizes physical cues over labels, camera movement relative to subject, and matching detail level to shot scale.[8]  

When comparing pipelines, these sources help you separate “prompt quality problems” from “graph/sampler problems,” since they define what *good* prompts look like regardless of whether you are using ComfyUI‑LTXVideo or your own repo.[4][8][10][5]

## General LTX‑Video / LTX‑2 how‑tos and tutorials

- NVIDIA Quick Start Guide For LTX-2 In ComfyUI – GPU‑oriented quick‑start showing how to run LTX‑2 efficiently on RTX hardware, with recommended settings for resolution, frame count, and performance.[9]
  - Useful as a reference for performance‑side differences when you configure your own pipelines vs. the default ComfyUI‑LTXVideo graphs.[9][1][2]

- How to run LTX Video 13B on ComfyUI (stable-diffusion-art.com) – Step‑by‑step ComfyUI i2v guide (older LTXV, but the workflow logic is similar).[13]
  - Valuable for understanding the typical ComfyUI lifecycle (download workflow, install nodes, wire models) that both ComfyUI‑LTXVideo and your LTX‑2 repo follow, even though the exact nodes differ for LTX‑2.[13][1][2]

- LTX Video: Ultimate Guide and 10 Powerful Tips for AI Videos (filmart.ai) – High‑level best practices for LTX video generation: pacing, motion strength, subject stability, and compositional advice.[14]
  - These tips translate cleanly to any LTX‑2 pipeline, ComfyUI or Python, because they are about what the model responds to rather than specific UIs.[14]

- LTX Video 2.0 Pro Image to Video Developer Guide (fal.ai) – API‑centric guide to integrating LTX Video 2.0 Pro, including optimization, latency/throughput considerations, and typical integration patterns.[6]
  - Helpful if you want to understand how to wrap your LTX‑2 graphs in services or compare your choices against a hosted implementation.[6]

## Video tutorials and community workflows

- ComfyUI Tutorial Series Ep 25: LTX Video (YouTube) – End‑to‑end walkthrough of installing the LTX‑Video model in ComfyUI and building t2v/i2v workflows.[7]
  - Closely mirrors the ComfyUI‑LTXVideo repo’s recommended graphs and is a good “visual diff” reference when you examine your own pipeline layout.[7][1][2]

- LTX Video (ComfyUI) Tutorial — Create AI Videos Using Vast.ai – Demonstrates running LTX Video via ComfyUI on rented GPUs, including VRAM management, speed vs. quality trade‑offs, and workflow setup.[15]
  - Again uses a graph style closer to ComfyUI‑LTXVideo; comparing this to your custom graphs highlights where you’ve added additional control or composition steps.[15][1][2]

- [Official Tutorial how to use LTX-2 - I2V & T2V on your local Comfy] (Reddit + linked video) – Community‑endorsed tutorial explicitly targeting LTX‑2 with both image‑to‑video and text‑to‑video workflows on local Comfy setups.[11]
  - Useful for seeing how power users adapt the official/ComfyUI pipelines, especially around chaining shots into longer sequences and managing seeds for continuity.[1][2][11]

If you want, the next step can be a more explicit pipeline‑level diff: node‑by‑node comparison between a stock ComfyUI‑LTXVideo graph and one of your LTX‑2 workflows, annotated with where each diverges from the canonical Python pipeline in Lightricks/LTX‑2.

[1](https://github.com/Lightricks/ComfyUI-LTXVideo)
[2](https://github.com/Lightricks/LTX-Video)
[3](https://comfyui-wiki.com/en/tutorial/advanced/ltx-video-workflow-step-by-step-guide)
[4](https://dev.to/gary_yan_86eb77d35e0070f5/ltx-2-prompting-guide-master-ai-video-generation-with-expert-techniques-2ejk)
[5](https://github.com/Lightricks/LTX-2)
[6](https://fal.ai/learn/devs/ltx-video-2-pro-image-to-video-developer-guide)
[7](https://www.youtube.com/watch?v=ftkjE0US7ZI)
[8](https://docs.ltx.video/api-documentation/prompting-guide)
[9](https://www.nvidia.com/en-us/geforce/news/rtx-ai-video-generation-guide/)
[10](https://ltx.io/model/ltx-2)
[11](https://www.reddit.com/r/StableDiffusion/comments/1q5cut2/official_tutorial_how_to_use_ltx2_i2v_t2v_on_your/)
[12](https://www.runcomfy.com/comfyui-nodes/ComfyUI-LTXTricks)
[13](https://stable-diffusion-art.com/ltxv-13b/)
[14](https://filmart.ai/ltx-video-ltxv/)
[15](https://www.youtube.com/watch?v=oOmzlgacLNw)
[16](https://ltx.studio/blog/ltx-2-the-complete-ai-creative-engine-for-video-production)
[17](https://www.lightricks.com/ltxv-documentation)
[18](https://ltx.io/model/api)
[19](https://www.ltx-2video.com)
[20](https://www.youtube.com/watch?v=B_Z94tBBEF4)
[21](https://ltx.video/blog/how-to-prompt-for-ltx-2)
[22](https://ltx.studio/blog-category/tutorials)
[23](https://www.nextdiffusion.ai/tutorials/how-to-run-ltx-video-13b-0-9-7-in-comfyui)
[24](https://ltx.studio)
[25](https://www.facebook.com/groups/stablediffusionuniverse/posts/1506737667225745/)
[26](https://videoeditorstudio.com/products/tutorial-toolkit)