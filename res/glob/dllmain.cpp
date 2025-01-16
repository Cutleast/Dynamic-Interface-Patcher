// Thanks to SkyHorizon for the code! Check out his profile on GitHub: https://github.com/SkyHorizon3

#include "pch.h"
#include <iostream>
#include <vector>
#include <string.h>
#include <regex>
#include <filesystem>

#define DLLEXPORT extern "C" __declspec(dllexport)

BOOL APIENTRY DllMain(HMODULE hModule,
					  DWORD ul_reason_for_call,
					  LPVOID lpReserved)
{
	switch (ul_reason_for_call)
	{
	case DLL_PROCESS_ATTACH:
	case DLL_THREAD_ATTACH:
	case DLL_THREAD_DETACH:
	case DLL_PROCESS_DETACH:
		break;
	}
	return TRUE;
}

std::string pattern_to_regex(const std::string &pattern)
{
	std::string regex_pattern;
	for (char c : pattern)
	{
		switch (c)
		{
		case '*':
			regex_pattern += ".*";
			break;
		case '?':
			regex_pattern += ".";
			break;
		case '.':
			regex_pattern += "\\.";
			break;
		default:
			regex_pattern += c;
		}
	}
	return regex_pattern;
}

static std::vector<std::string> stringResult;
static std::vector<const char *> returnValues;

DLLEXPORT void glob_clear()
{
	returnValues.clear();
	stringResult.clear();
}

DLLEXPORT const char **glob_cpp(const char *pattern, const char *basePath, bool recursive, size_t *out_size)
{
	glob_clear();

	std::regex pattern_regex(pattern_to_regex(pattern));

	auto checkFile = [&pattern_regex](const std::filesystem::directory_entry &entry)
	{
		if (entry.is_regular_file())
		{
			const auto &fileName = entry.path().filename().string();
			return std::regex_match(fileName, pattern_regex);
		}
		return false;
	};

	if (recursive)
	{
		for (const auto &entry : std::filesystem::recursive_directory_iterator(basePath))
		{
			if (checkFile(entry))
			{
				stringResult.emplace_back(entry.path().string());
			}
		}
	}
	else
	{
		for (const auto &entry : std::filesystem::directory_iterator(basePath))
		{
			if (checkFile(entry))
			{
				stringResult.emplace_back(entry.path().string());
			}
		}
	}

	for (const auto &str : stringResult)
	{
		returnValues.emplace_back(str.c_str());
	}

	*out_size = returnValues.size();
	return returnValues.data();
}