extends RefCounted


static func checker_texture(resolution: int) -> Dictionary:
	var image := Image.create(resolution, resolution, false, Image.FORMAT_RGBA8)
	var checksum := 0
	for y in range(resolution):
		for x in range(resolution):
			var bright := ((x / 4) + (y / 4)) % 2 == 0
			var byte_value := 255 if bright else 158
			var value := float(byte_value) / 255.0
			checksum = int((checksum + ((x + 1) * 31 + (y + 1) * 17) * byte_value) % 2147483647)
			image.set_pixel(x, y, Color(value, value, value, 1.0))
	return {
		"texture": ImageTexture.create_from_image(image),
		"checksum": checksum,
	}


static func texture_bytes(resolution: int, bytes_per_pixel: int) -> int:
	return resolution * resolution * bytes_per_pixel


static func production_atlas(resolution: int, slot: StringName) -> Texture2D:
	var image := Image.create(resolution * 4, resolution, false, Image.FORMAT_RGBA8)
	var base := [
		Color(0.40, 0.62, 0.22, 1.0),
		Color(0.42, 0.43, 0.42, 1.0),
		Color(0.63, 0.53, 0.36, 1.0),
		Color(0.30, 0.30, 0.32, 1.0),
	]
	for y in range(resolution):
		for x in range(resolution * 4):
			var tile := int(x / resolution)
			var color: Color = base[tile]
			if slot == &"normal":
				color = Color(0.5, 0.5, 1.0, 1.0)
			elif slot == &"roughness_orm":
				color = Color(0.0, 0.76 + float(tile) * 0.04, 1.0, 1.0)
			else:
				var grain := 0.90 + 0.10 * float(((x * 13 + y * 7 + tile * 19) % 11)) / 10.0
				color = Color(color.r * grain, color.g * grain, color.b * grain, 1.0)
			image.set_pixel(x, y, color)
	return ImageTexture.create_from_image(image)
