# SVD Studio

An interactive Streamlit app that shows how the **Singular Value Decomposition (SVD)** compresses, denoises and explains images.
Built as a Linear Algebra mini project for **PES University, UE25MA242A**.

**Live demo:** <PASTE YOUR STREAMLIT URL HERE>

## What it does

| Tab | What you see |
|---|---|
| **Compress** | Drag-to-compare slider (original vs rank-k image), error map, singular value spectrum, download button |
| **Build-up** | Animated rebuild of the image from rank-1 layers `A = σ₁u₁v₁ᵀ + σ₂u₂v₂ᵀ + …` |
| **The math, stage by stage** | Matrix → RREF → Rank & Nullity → Gram-Schmidt → Projection → Eigen/Diagonalization |
| **Projection lab** | Least squares on a single image column, with the residual shown to be orthogonal |
| **Denoise** | Truncated SVD as a low-pass filter, with PSNR vs k |
| **Sweet spot** | Quality (PSNR) vs compression ratio, pick the smallest k for a target quality |

Extras: three themes (Blue / Green / Red pill), Matrix digital rain in the header, colour or grayscale mode, upload your own image.

## Linear algebra concepts covered

- Image as an m×n matrix
- Gaussian elimination and RREF
- Rank and nullity
- Gram-Schmidt orthogonalization
- Orthogonal projection `P = UₖUₖᵀ` and least squares
- Eigenvalues of the symmetric matrix `AᵀA` (`λᵢ = σᵢ²`)
- Eckart-Young theorem: truncated SVD is the best rank-k approximation

## Run locally

```bash
git clone https://github.com/<your-username>/svd-studio.git
cd svd-studio

python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

## Project structure

```
svd-studio/
├── app.py                 # the whole app
├── requirements.txt
├── .streamlit/
│   └── config.toml        # dark theme
├── README.md
├── LICENSE
└── .gitignore
```

## Deployment

Hosted on **Streamlit Community Cloud** (free). Streamlit apps need a long-running Python server with websockets, so serverless hosts such as Vercel cannot run them.

## Tech stack

Python, Streamlit, NumPy, Matplotlib, Pillow, scikit-image

## Author

<YOUR NAME> · PES University
