
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class models_c
	{
	public:

		std::vector<structures::model_s> models;

		bool load();
		void destroy();
		std::uint64_t strip();
		structures::model_s* find(const char* name);
		const structures::model_part_s* part(const structures::model_s& model, const char* name);
		bool upload(structures::model_s& model);
		structures::model_s* clone(const char* source, const char* name, structures::vec3_s tint, std::float_t metal);
		structures::model_s* create(const char* name);
		structures::model_s* existing(const char* name);
		std::uint32_t variant(std::uint32_t material, structures::vec3_s tint, std::float_t metal);
		void begin_part(structures::model_s& model, const char* name);
		void append(structures::model_s& model, const structures::model_s& source, const structures::model_part_s& part, const structures::mat4_s& placement, std::uint32_t material, std::float_t keep, std::uint32_t salt);
		void sphere(structures::model_s& model, structures::vec3_s center, std::float_t radius, std::uint32_t material);
		void seal(structures::model_s& model);
	};

	extern models_c models;
}

//=====================================================================================
