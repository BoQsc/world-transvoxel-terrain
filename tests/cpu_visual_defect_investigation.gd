extends SceneTree

const Runner := preload("res://tests/cpu_visual_defect_investigation_runner.gd")


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var runner := Runner.new()
	root.add_child(runner)
	var exit_code: int = await runner.finished
	runner.queue_free()
	quit(exit_code)
