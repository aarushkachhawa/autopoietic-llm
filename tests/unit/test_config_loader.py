import yaml

from autopoietic.config.loader import apply_dotted_override, load_config


def test_defaults_with_no_file():
    cfg = load_config()
    assert cfg.task.task_set == "coding_katas"
    assert cfg.model.temp == 0.2


def test_load_single_file(tmp_path):
    cfg_path = tmp_path / "base.yaml"
    cfg_path.write_text(yaml.dump({"data_dir": "mydata", "model": {"path": "foo"}}))
    cfg = load_config(cfg_path)
    assert str(cfg.data_dir) == "mydata"
    assert cfg.model.path == "foo"


def test_layered_override_preserves_unrelated_fields(tmp_path):
    base = tmp_path / "base.yaml"
    base.write_text(yaml.dump({"model": {"path": "base-model", "temp": 0.5}}))
    override = tmp_path / "override.yaml"
    override.write_text(yaml.dump({"model": {"path": "override-model"}}))

    cfg = load_config([base, override])
    assert cfg.model.path == "override-model"
    assert cfg.model.temp == 0.5


def test_apply_dotted_override():
    data: dict = {}
    apply_dotted_override(data, "model.path", "x")
    assert data == {"model": {"path": "x"}}
