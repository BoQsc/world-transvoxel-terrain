extends SceneTree

const RUNNER_PATH := "res://tests/cpu_prefetch_readiness_runner.gd"


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var runner_script := load(RUNNER_PATH) as Script
	if runner_script == null or not runner_script.can_instantiate():
		push_error("CPU prefetch readiness runner could not be instantiated")
		quit(1)
		return
	var runner: Node = runner_script.new()
	root.add_child(runner)
	var exit_code: int = await runner.finished
	runner.queue_free()
	quit(exit_code)
