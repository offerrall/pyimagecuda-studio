from pyimagecuda_studio import LoadProject, run, set_node_parameter

with LoadProject("sign.pics"):
    for i in range(1, 11):
        set_node_parameter("Text", "text", f"Test {i}")
        run(f"output_{i:02d}.png")