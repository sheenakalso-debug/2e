from amazon_pc_finder.specs import evaluate_specs, extract_cpu, extract_gpu, extract_ram_gb


def test_baseline_cpu_meets_bar():
    match = evaluate_specs("Desktop with Intel Core i5-8400 CPU, 16GB RAM, GTX 1660 GPU")
    assert match.meets_cpu
    assert match.cpu_found == "i5-8400"


def test_baseline_amd_cpu_meets_bar():
    match = evaluate_specs("PC with AMD Ryzen 5 2600, 16GB RAM, RX 5500 XT")
    assert match.meets_cpu
    assert match.cpu_found == "ryzen 5 2600"


def test_weaker_cpu_fails():
    match = evaluate_specs("PC with Intel Core i3-8100, 16GB RAM, GTX 1660")
    assert not match.meets_cpu


def test_stronger_cpu_passes():
    match = evaluate_specs("PC with Intel Core i7-10700, 16GB RAM, RTX 3060")
    assert match.meets_cpu
    assert match.meets_gpu


def test_gpu_baseline_and_stronger():
    assert extract_gpu("NVIDIA GTX 1660 6GB")[1] == 100
    assert extract_gpu("AMD Radeon RX 5500 XT 8GB")[1] == 100
    assert extract_gpu("NVIDIA RTX 3060 12GB")[1] > 100


def test_weaker_gpu_fails():
    match = evaluate_specs("Intel i5-8400, 16GB RAM, GTX 1650")
    assert not match.meets_gpu


def test_ram_extraction_variants():
    assert extract_ram_gb("16GB RAM") == 16
    assert extract_ram_gb("RAM: 12GB") == 12
    assert extract_ram_gb("Memory: 32GB DDR4") == 32
    assert extract_ram_gb("512GB SSD, 16GB RAM") == 16


def test_ram_below_minimum_fails():
    match = evaluate_specs("Intel i5-8400, 8GB RAM, GTX 1660")
    assert not match.meets_ram


def test_all_specs_met():
    match = evaluate_specs(
        "Gaming Desktop, AMD Ryzen 5 3600, 16GB DDR4 RAM, NVIDIA GTX 1660 Super, 500GB SSD"
    )
    assert match.meets_all


def test_no_gpu_detected():
    match = evaluate_specs("Office PC, Intel i5-8400, 16GB RAM, Integrated Graphics")
    assert not match.meets_gpu
    assert match.gpu_found is None


def test_cpu_f_variant_matches_exact_key():
    match = extract_cpu("Desktop with Intel Core i5-9400F processor")
    assert match is not None
    assert match[0] == "i5-9400f"


def test_cpu_word_boundary_does_not_overmatch():
    # "i5-8400" must not match inside an unrelated longer model number.
    assert extract_cpu("some obscure part number ax58400xz") is None
