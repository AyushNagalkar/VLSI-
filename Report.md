UST – USE CASE 5: Hybrid AI–EDA
Workflow for Floor Planning
Report By AI Team
Team Members: Rushiraj Suwarnkar, Rushikesh More, Ayush Nagalkar
Guided By: Dr. Anuradha Yenkikar, Dr. Abhay Chopde
Overview:
This project presents a Hybrid AI–EDA workflow for floorplanning, where Artificial
Intelligence (AI) is integrated with traditional Electronic Design Automation (EDA) tools to
improve placement quality and reduce manual effort. Instead of replacing EDA tools, the
system uses AI as an intelligent guidance layer to generate placement strategies, which are
later refined and validated by tools like Innovus and OpenROAD.
The workflow combines Graph Neural Networks (GNNs), generative placement models,
and TCL-based automation, along with a feedback-driven optimization loop. Experiments
on CircuitNet, FloorSet, and UART datasets show that the approach can learn placement
patterns, improve congestion and timing metrics, and produce scalable and explainable
floorplanning solutions.
Introduction:
Floorplanning is one of the most critical stages in VLSI physical design, directly affecting
performance, power, and chip area. Traditional methods rely on heuristic-based algorithms
and manual tuning, which are time-consuming and difficult to scale for modern complex
designs.
Recent AI-based approaches attempt to automate placement, but they often face challenges
such as lack of physical legality, poor interpretability, and weak integration with industry
tools.
To address these issues, this project proposes a Hybrid AI–EDA workflow, where:
• AI predicts placement strategies
• EDA tools ensure physical correctness and sign-off quality
• The system maintains explainability and reproducibility
This approach bridges the gap between research-level AI models and real-world chip design
workflows.
Architecture:
The system follows a modular pipeline consisting of:
1. Design Input Layer
• Verilog Netlist
• LEF Files
• SDC Constraints
• Liberty Files
2. Feature Extraction Layer
• Graph-based representation of circuit
• Node features (area, connectivity, type)
• Timing and congestion features
3. AI Floorplanning Engine
• GNN Encoder for learning connectivity
• Generative model for placement strategy
• Outputs relative placement decisions
4. TCL Script Generation
• Converts AI outputs into executable TCL commands
• Ensures compatibility with EDA tools
5. EDA Execution Layer
• Tools: OpenROAD, Innovus, DREAMPlace
• Performs placement refinement, routing, and validation
6. Feedback Loop
• Multi-agent system:
o Timing Agent
o Congestion Agent
o Power Agent
• Iteratively improves placement quality
Methodology:
The workflow is executed in the following steps:
1. Input Processing
Design files (netlist, LEF, SDC) are parsed and converted into structured data.
2. Graph Construction
The circuit is represented as a graph where:
o Nodes = cells/macros
o Edges = connectivity
3. Feature Engineering
Extract features such as:
o Connectivity (fan-in, fan-out)
o Physical properties (area, size)
o Timing criticality
4. Model Training
o GNN models are trained to learn placement patterns
o Hybrid loss functions used (topology + quality)
5. Placement Prediction
o Model predicts (x, y) coordinates or placement strategies
6. TCL Generation
o Predictions converted into Innovus-compatible scripts
7. EDA Execution & Evaluation
o Placement is refined using EDA tools
o Metrics such as congestion, timing, and power are evaluated
8. Feedback Optimization
o Results are used to iteratively improve the model
Current Implementation:
We have implemented three different AI-based floorplanning models on three datasets,
each targeting different levels of design complexity and placement granularity. This multimodel approach allows us to validate the robustness, scalability, and adaptability of the
proposed Hybrid AI–EDA workflow.
1. CircuitNet-Based Model
Dataset: CircuitNet (28nm technology)
Design Scale: ~52,000 cells, ~434,000 edges
Key Work
• Constructed a large-scale graph representation of the circuit:
o Nodes → standard cells and macros
o Edges → net-based connectivity
• Implemented efficient edge construction strategies:
o Net-based connections
o Star topology for large nets (to avoid quadratic complexity)
• Designed a 16-dimensional feature vector capturing:
o Spatial features (position, area)
o Connectivity features (fanout, pin count)
o Structural importance
• Trained Graph Neural Network models (GCN/GAT) using PyTorch Geometric
• Used MSE loss to predict placement coordinates
Technical Strengths
• Handles very large graphs efficiently
• Captures global connectivity patterns using message passing
• Preserves real netlist relationships
Observations
• The model successfully learns spatial placement patterns from connectivity
• Macros dominate placement decisions due to:
o Larger physical area
o Higher connectivity
• Connectivity features have the highest impact on prediction accuracy
Limitations (Specific to this Model)
• Limited macro diversity in dataset
• No direct integration with physical design formats like DEF
• Predictions are not yet validated through full EDA flow
Results and Ouputs:
2. UART-Based Model (Dataset Provided by ENTC Team)
Dataset: Provided by ENTC team
Design Size: ~130 cells
Additional Data: 1,170 experimental placement configurations
Key Work
• Built a complete end-to-end pipeline:
o Verilog netlist parsing
o Graph construction using NetworkX
o SDC parsing for timing constraints
• Introduced timing-aware feature engineering:
o Extracted clock constraints and critical paths
o Computed cell-level timing criticality scores
• Designed a 10-dimensional feature vector:
o 8 connectivity features
o 2 timing-aware features
Advanced Enhancements
• Implemented hybrid training strategy:
o 70% topology-based (spring layout)
o 30% real performance data (CSV metrics)
• Processed 1,170 experimental runs to extract:
o Congestion
o Timing slack
o Power consumption
o Overall quality score
Model Architecture
• 3-layer Graph Convolution Network (GCN)
• Hidden layers: 64 → 64 → 32
• Dual-output head:
o Placement prediction → (x, y) coordinates
o Quality prediction → confidence score (0–1)
Outputs
• Generated placement coordinates for each cell
• Converted predictions into Innovus-compatible TCL scripts:
o place_cell
o create_rect
o set_block_status
Insights
• Timing-aware features significantly improve placement decisions
• Hybrid training improves generalization and real-world applicability
• Confidence score helps identify uncertain predictions
Results and Output:

3. FloorSet-Based Model
Dataset: FloorSet (macro-level floorplanning dataset)
Key Work
• Focused on macro placement, which has the highest impact on floorplanning quality
• Used Graph Attention Network (GAT) instead of GCN:
o Allows model to learn importance weights for different connections
• Trained model to predict macro placement strategies rather than exact coordinates
• Integrated with OpenROAD for placement validation
Technical Advantages
• Attention mechanism improves:
o Handling of complex connectivity
o Identification of critical macros
• Better suited for hierarchical and macro-dominated designs
Results
• Achieved approximately 90% accuracy in placement prediction
• Improved:
o Macro alignment
o Placement distribution
o Congestion handling
Practical Impact
• Demonstrates that AI can effectively handle macro-level floorplanning, which is one
of the hardest parts of physical design
• Shows strong potential for industry-scale adoption
Output TCL: Drive link to compare normal tcl and ai tcl:
https://drive.google.com/drive/folders/1HYJJaP8l7rlkpQNcjnFdU52WZPvp8Oxu?usp=drive
_link
Work Done Till Now:
• Built complete data processing and graph pipeline
• Implemented feature engineering with timing awareness
• Trained GNN models on three different datasets
• Generated placement predictions and TCL scripts
• Integrated workflow with OpenROAD and Innovus (partial)
• Prepared evaluation framework for comparison with baseline
Current Limitations:
• Limited testing on real industrial-scale netlists
• No full DEF-level integration yet predicting placement and generaete
• Model generalization across designs is still limited
• Feedback loop is not fully automated
Next Steps:
• Train and test on different real-world designs
• Fine-tune models using more data which will provided by ENTC team
• Improve model parameters and architecture (GAT/Transformer)
• Integrate flow with Innovus

Expected Outcomes by Internship End (Realistic and Achievable):

Must-Achieve Outcomes:
• Deliver a complete Hybrid AI-EDA prototype where AI generates initial floorplanning/placement guidance and EDA tools refine and validate physical legality.
• Demonstrate reproducible end-to-end runs from input parsing -> graph construction -> model inference -> TCL/placement artifact generation -> EDA evaluation.
• Produce dataset-wise benchmark comparisons (CircuitNet, UART, FloorSet) using consistent metrics such as wirelength proxy, congestion indicators, timing-aware score, overlap/density, and runtime.
• Show measurable reduction in manual trial-and-error during early placement exploration by providing AI-generated candidate strategies.
• Generate Innovus/OpenROAD-compatible outputs (TCL and placement-related artifacts) for downstream physical design flow integration.
• Provide explainable model behavior at practical level (feature importance trends, confidence score use, macro-priority behavior).
• Publish a final technical package containing trained models, scripts, notebooks, metrics reports, and clear reproduction steps.

Stretch Outcomes (Possible if Time and Data Permit):
• Improve cross-design generalization with additional training data and hyperparameter tuning.
• Build a semi-automated feedback loop that updates model guidance based on post-EDA timing/congestion/power evaluation.
• Improve macro-level placement quality consistency across unseen test designs.
• Add stronger timing-aware and congestion-aware loss balancing for better practical QoR trends.

Explicit Non-Goals (To Avoid Overclaiming):
• Full autonomous sign-off placement by neural network alone without EDA refinement.
• Guaranteed QoR improvement over traditional EDA flow on every design and corner.
• Immediate replacement of commercial placement engines for tapeout-grade closure.
• Fully automated industrial-scale feedback optimization loop across all design classes within internship timeline.

Final Project Positioning:
This internship project should be positioned as an AI-augmented floorplanning accelerator, not an EDA replacement. The core success criterion is practical integration: AI improves the quality and speed of initial placement decisions, while EDA tools ensure physical correctness and sign-off reliability.