# List projects + their completion status
vtx projects list
vtx projects status <slug>

# Create a new project from template
vtx projects new <slug> --title "..."

# Create/activate per-project venv
vtx project env-create <slug>

# Generate story artifacts (OpenAI optional)
vtx story outline <slug>
vtx story screenplay <slug>
vtx story shotlist <slug>
vtx story clips <slug>

# Render
vtx render clip <slug> A01_S01_SH001
vtx render scene <slug> A01_S01
vtx render act <slug> A01
vtx render all <slug> --resume

# Assemble
vtx assemble act <slug> A01
vtx assemble final <slug>
