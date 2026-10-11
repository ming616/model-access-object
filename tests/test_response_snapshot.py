import json

from model_access_object import ModelAccessResponse


def test_response_snapshot_detaches_nested_values_for_task_checkpoint():
    response = ModelAccessResponse(
        "draft", model="model", connector_id="connector", usage={"tokens": 3},
        metadata={"request_metadata": {"task_id": "task", "work_id": "draft-1",
                                       "attempt_id": "attempt"}},
    )
    snapshot = response.to_dict()
    assert json.loads(json.dumps(snapshot))["metadata"]["request_metadata"]["task_id"] == "task"
    snapshot["usage"]["tokens"] = 99
    snapshot["metadata"]["request_metadata"]["task_id"] = "changed"
    assert response.usage == {"tokens": 3}
    assert response.metadata["request_metadata"]["task_id"] == "task"
