import ebpfStorageIO
import GenerateWorkload

ebpf_workload_dict = {
    'Workload_Parcing_logic': ebpfStorageIO.ebpStorageIO(),
}

generated_workload_dict = {
    'Workload_Parcing_logic': GenerateWorkload.GnerateWorkloadType(),
}
Workload_type_dictionary={
    'ebpf':ebpf_workload_dict,
    'Generated':generated_workload_dict,
}

