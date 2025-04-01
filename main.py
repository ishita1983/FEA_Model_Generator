import io
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

def generate_abaqus_input(diameter, thickness, height, youngs_modulus, element_size):
    radius = diameter / 2
    num_circumferential_elements = int((3.1416 * diameter) / element_size)
    num_vertical_elements = int(height / element_size)

    output = io.StringIO()
    output.write("** Abaqus Input File for Shell Model of a Vessel\n")
    output.write("*Heading\n")
    output.write("Pressure Vessel Model\n\n")
    output.write("*Part, name=Vessel\n")
    output.write("*Node\n")

    node_id = 1
    nodes = {}
    node_coordinates = []

    for i in range(num_vertical_elements + 1):
        z = i * element_size
        for j in range(num_circumferential_elements):
            theta = (j / num_circumferential_elements) * 360.0
            x = radius * np.cos(np.radians(theta))
            y = radius * np.sin(np.radians(theta))
            output.write(f"{node_id}, {x:.3f}, {y:.3f}, {z:.3f}\n")
            nodes[(i, j)] = node_id
            node_coordinates.append((x, y, z))  # Store for visualization
            node_id += 1

    output.write("*Element, type=S4\n")
    element_id = 1
    for i in range(num_vertical_elements):
        for j in range(num_circumferential_elements):
            n1 = nodes[(i, j)]
            n2 = nodes[(i, (j + 1) % num_circumferential_elements)]
            n3 = nodes[(i + 1, (j + 1) % num_circumferential_elements)]
            n4 = nodes[(i + 1, j)]
            output.write(f"{element_id}, {n1}, {n2}, {n3}, {n4}\n")
            element_id += 1

    output.write("*End Part\n\n")
    output.write("*Material, name=Steel\n")
    output.write("*Elastic\n")
    output.write(f"{youngs_modulus}, 0.3\n\n")
    output.write(f"*Shell Section, elset=ALL_ELEMENTS, material=Steel, thickness={thickness}\n")
    output.write("*Assembly, name=Assembly\n")
    output.write("*Instance, name=Vessel-1, part=Vessel\n")
    output.write("*End Instance\n")
    output.write("*End Assembly\n\n")
    output.write("*Step, name=StaticStep, nlgeom=YES\n")
    output.write("*Static\n")
    output.write("1.0, 1.0, 1e-05, 1.0\n\n")
    output.write("*End Step\n")

    inp_content = output.getvalue()
    output.seek(0)
    byte_data = io.BytesIO(inp_content.encode('utf-8')).getvalue()

    return inp_content, byte_data, node_coordinates  # Return nodes as well


st.title("Abaqus Input File Generator :rocket:")

# Sidebar for user inputs
st.sidebar.header("Input Parameters")
diameter = st.sidebar.number_input("Shell Diameter (inches)", value=120.0)
thickness = st.sidebar.number_input("Shell Thickness (inches)", value=1.125)
height = st.sidebar.number_input("Shell Length (inches)", value=270.0)
youngs_modulus = st.sidebar.number_input("Material Young's Modulus (PSI)", value=29000000.0, format="%.0f")
element_size = st.sidebar.number_input("Element Size (inches)", value=6.0)

# Generate Abaqus input file
if st.sidebar.button("Generate Abaqus Input File"):
    with st.spinner("Generating Abaqus input file..."):
        inp_content, inp_file, node_coordinates = generate_abaqus_input(diameter, thickness, height, youngs_modulus, element_size)

        col1, col2 = st.columns([1, 1])  # Equal width columns

        with col1:
            st.subheader("Generated Abaqus Input File")
            st.text_area("Abaqus Input File:", inp_content, height=600)
            st.download_button(
                label="Download Abaqus Input File",
                data=inp_file,
                file_name="vessel.inp",
                mime="text/plain"
            )

        with col2:
            st.subheader("Mesh Visualization")

            # Convert node list to NumPy arrays
            x_vals, y_vals, z_vals = zip(*node_coordinates)
            x_vals, y_vals, z_vals = np.array(x_vals), np.array(y_vals), np.array(z_vals)

            # Reshape data into a structured grid
            num_circumferential = int((np.max(x_vals) - np.min(x_vals)) / element_size)
            num_vertical = int((np.max(z_vals) - np.min(z_vals)) / element_size)

            theta = np.linspace(0, 2 * np.pi, num_circumferential)
            z_grid = np.linspace(0, np.max(z_vals), num_vertical)
            theta, z_grid = np.meshgrid(theta, z_grid)

            X = (diameter / 2) * np.cos(theta)
            Y = (diameter / 2) * np.sin(theta)
            Z = z_grid

            # Create a surface plot
            fig = go.Figure()

            fig.add_trace(
                go.Surface(
                    x=X, y=Y, z=Z,
                    colorscale="Viridis",
                    opacity=0.9,  # Slight transparency
                    contours={
                        "x": {"show": True, "color": "black", "width": 1},
                        "y": {"show": True, "color": "black", "width": 1},
                        "z": {"show": True, "color": "black", "width": 1},
                    }
                )
            )

            # Add wireframe grid using Scatter3d (node connections)
            for i in range(num_vertical):
                fig.add_trace(go.Scatter3d(
                    x=X[i, :], y=Y[i, :], z=Z[i, :],
                    mode="lines",
                    line=dict(color="black", width=2),
                    showlegend=False
                ))

            for j in range(num_circumferential):
                fig.add_trace(go.Scatter3d(
                    x=X[:, j], y=Y[:, j], z=Z[:, j],
                    mode="lines",
                    line=dict(color="black", width=2),
                    showlegend=False
                ))

            fig.update_layout(
                scene=dict(
                    xaxis_title="X",
                    yaxis_title="Y",
                    zaxis_title="Z"
                ),
                title="Generated Mesh Surface with Node Connections",
                height=800,
            )

            st.plotly_chart(fig)

        st.success("Abaqus input file generated successfully!")


