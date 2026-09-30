
//=====================================================================================

#pragma once

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	class jobs_c
	{
	public:

		std::vector<std::thread> workers;
		std::mutex mutex;
		std::condition_variable wake;
		std::condition_variable finished;
		std::function<void(std::uint32_t)> task;
		std::atomic<std::uint32_t> next_index{ 0u };
		std::atomic<std::uint32_t> completed{ 0u };
		std::uint32_t task_count = 0u;
		std::uint32_t active = 0u;
		std::uint64_t generation = 0u;
		bool running = false;

		std::uint32_t thread_count()
		{
			return static_cast<std::uint32_t>(workers.size()) + 1u;
		}

		void start()
		{
			running = true;

			for (auto index{ 1u }; index < std::max(2u, std::thread::hardware_concurrency()); index++)
			{
				workers.emplace_back([this]() { worker(); });
			}
		}

		void stop()
		{
			{
				std::lock_guard<std::mutex> guard{ mutex };

				running = false;
			}

			wake.notify_all();

			for (auto& thread : workers)
			{
				thread.join();
			}

			workers.clear();
		}

		void worker()
		{
			auto seen{ 0ull };

			std::unique_lock<std::mutex> lock{ mutex };

			while (running)
			{
				wake.wait(lock, [&]() { return !running || generation != seen; });

				if (running && generation != seen)
				{
					seen = generation;

					active++;

					lock.unlock();

					execute();

					lock.lock();

					active--;

					finished.notify_all();
				}
			}
		}

		void execute()
		{
			for (auto index{ next_index.fetch_add(1u) }; index < task_count; index = next_index.fetch_add(1u))
			{
				task(index);

				completed.fetch_add(1u);
			}
		}

		void parallel_for(std::uint32_t count, const std::function<void(std::uint32_t)>& function)
		{
			if (count)
			{
				{
					std::unique_lock<std::mutex> lock{ mutex };

					finished.wait(lock, [&]() { return active == 0u; });

					task = function;

					task_count = count;

					next_index = 0u;

					completed = 0u;

					generation++;
				}

				wake.notify_all();

				execute();

				std::unique_lock<std::mutex> lock{ mutex };

				finished.wait(lock, [&]() { return completed.load() >= task_count && active == 0u; });
			}
		}
	};

	inline jobs_c jobs;
}

//=====================================================================================
