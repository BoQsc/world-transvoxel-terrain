extends Node

const Runner := preload("res://tests/tqp57_large_terrain_acceptance_runner.gd")


func _ready() -> void:
	var runner := Runner.new()
	add_child(runner)
	var exit_code: int = await runner.finished
	runner.queue_free()
	get_tree().quit(exit_code)
