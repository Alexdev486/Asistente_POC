from app.modules.tree_engine.service import DiagnosticTreeEngine


def test_tree_engine_advances_to_diagnosis() -> None:
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {"type": "question", "text": "Arranca?", "answers": {"si": "n2", "no": "n3"}},
            "n2": {"type": "diagnosis", "result": "Bateria descargada"},
            "n3": {"type": "diagnosis", "result": "Motor de arranque"},
        },
    }

    engine = DiagnosticTreeEngine()
    first = engine.start(tree)
    assert first.node_type == "question"
    assert first.question == "Arranca?"

    second = engine.advance(tree, first.node_id, "si")
    assert second.node_type == "diagnosis"
    assert second.diagnosis == "Bateria descargada"
