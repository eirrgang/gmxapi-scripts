"""
Runner for adaptive MSMs
"""

import gmx
import analysis

# Add a TPR-loading operation to the default work graph (initially empty) that
# produces simulation input data bundle (parameters, structure, topology)

N = 50  # Number of ensemble members
starting_structure = 'input_conf.gro' # Could start with a list of distinct confs
topology_file = 'input.top'
run_parameters = 'params.mdp'

initial_tpr = gmx.commandline_operation('gmx', 'grompp',
                                        input={'-f': run_parameters,
                                        '-p': topology_file,
                                        '-c': starting_structure})
initial_input = gmx.load_tpr([initial_tpr] * N)  # An array of simulations

# Get a placeholder object that can serve as a sub context / work graph owner
# and can be used in a control operation.
subgraph = gmx.subgraph(input={'conformation': initial_input})

with subgraph:
    modified_input = gmx.modify_input(
        input=initial_input, structure=subgraph.conformation)
    md = gmx.mdrun(input=modified_input)
    # Assume the existence of a more integrated gmx.trajcat operation
    cluster = gmx.command_line(
        'gmx', 'cluster', input=gmx.reduce(gmx.trajcat, md.output.trajectory))
    # rmsd = gmx.command_line(
    #     'gmx', 'rmsdist', input=gmx.reduce(gmx.trajcat, md.output.trajectory))
    condition = analysis.cluster_analyzer(
        input=cluster.output.file["-cl"])

# In the default work graph, add a node that depends on `condition` and
# wraps subgraph.
my_loop = gmx.while_loop(gmx.logical_not(condition.is_converged), subgraph)

gmx.run()