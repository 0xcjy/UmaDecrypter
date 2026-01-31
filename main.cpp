#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <iomanip> // For std::hex, std::setw, std::setfill
#include <fstream> // For file operations
#include <filesystem> // For path operations (C++17)
#include <chrono> // For timing

#include "json.hpp"
using json = nlohmann::json;

// Helper function to load JSON from a file
json load_json_from_file(const std::filesystem::path& file_path) {
    std::ifstream i(file_path);
    if (!i.is_open()) {
        std::cerr << "Error: Could not open JSON file " << file_path << std::endl;
        return nullptr;
    }
    json j;
    try {
        i >> j;
    } catch (const json::parse_error& e) {
        std::cerr << "Error: JSON parse error in " << file_path << ": " << e.what() << std::endl;
        return nullptr;
    }
    return j;
}

// Global constants (from Python's main.py)
const std::string DB_KEY_STR = "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd";
const std::string AB_KEY_STR = "532B4631E4A7B9473E7CFB";
const std::string JSON_FILE = "meta.json";
const std::string CONFIG_FILE = "config.json";

// Helper function to convert a hex string to a byte vector
std::vector<unsigned char> hex_to_bytes(const std::string& hex) {
    std::vector<unsigned char> bytes;
    for (size_t i = 0; i < hex.length(); i += 2) {
        std::string byteString = hex.substr(i, 2);
        unsigned char byte = static_cast<unsigned char>(std::stoul(byteString, nullptr, 16));
        bytes.push_back(byte);
    }
    return bytes;
}

// Helper function to convert a byte vector to a hex string
std::string bytes_to_hex_string(const std::vector<unsigned char>& bytes) {
    std::stringstream ss;
    ss << std::hex << std::setfill('0');
    for (unsigned char b : bytes) {
        ss << std::setw(2) << static_cast<int>(b);
    }
    return ss.str();
}

// Helper function to convert a long long to an 8-byte little-endian vector
std::vector<unsigned char> int_to_little_endian_bytes(long long value) {
    std::vector<unsigned char> bytes(8);
    for (int i = 0; i < 8; ++i) {
        bytes[i] = (value >> (i * 8)) & 0xFF;
    }
    return bytes;
}

// Implements Python's get_final_key function
std::vector<unsigned char> get_final_key(long long key_int) {
    std::vector<unsigned char> base_key = hex_to_bytes(AB_KEY_STR);
    std::vector<unsigned char> keys_bytes = int_to_little_endian_bytes(key_int);
    std::vector<unsigned char> final_key;
    final_key.reserve(base_key.size() * keys_bytes.size()); // Pre-allocate memory

    for (size_t i = 0; i < base_key.size(); ++i) {
        for (size_t j = 0; j < keys_bytes.size(); ++j) { // keys_bytes.size() is 8
            final_key.push_back(base_key[i] ^ keys_bytes[j]);
        }
    }
    return final_key;
}

// Implements Python's decrypt_core function
std::vector<unsigned char> decrypt_core(const std::vector<unsigned char>& data, const std::vector<unsigned char>& key) {
    if (key.empty()) {
        return data; // No key, return original data
    }

    std::vector<unsigned char> decrypted_data(data.size());
    size_t key_len = key.size();

    for (size_t i = 0; i < data.size(); ++i) {
        decrypted_data[i] = data[i] ^ key[i % key_len];
    }
    return decrypted_data;
}

// Helper function to join paths
std::filesystem::path join_paths(const std::filesystem::path& base, const std::string& path_segment) {
    return base / path_segment;
}

// Helper function to check if a file exists
bool file_exists(const std::filesystem::path& p) {
    return std::filesystem::is_regular_file(p);
}

// Implements Python's decrypt_ab function
std::vector<unsigned char> decrypt_ab(const std::filesystem::path& ab_path, const std::string& key_hex) {
    std::ifstream file(ab_path, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file " << ab_path << std::endl;
        return {}; // Return empty vector on error
    }

    std::streamsize size = file.tellg();
    file.seekg(0, std::ios::beg);

    std::vector<unsigned char> data(size);
    if (file.read(reinterpret_cast<char*>(data.data()), size)) {
        if (key_hex.empty()) {
            return data;
        }
        if (data.size() <= 256) {
            return data;
        }
        std::vector<unsigned char> key_bytes = hex_to_bytes(key_hex);
        return decrypt_core(data, key_bytes);
    } else {
        std::cerr << "Error: Could not read file " << ab_path << std::endl;
        return {}; // Return empty vector on error
    }
}

int main() {
#ifdef _WIN32
    system("chcp 65001"); // Set console code page to UTF-8 on Windows
#endif
    std::cout << "UmaDecryptor C++ Version" << std::endl;

    // Load config.json
    json config = load_json_from_file(CONFIG_FILE);
    if (config.is_null()) {
        return 1; // Error loading config.json
    }

    std::string decryption_strategy = config.value("decryption_strategy", "2");
    long long last_index = config.value("last_index", 0LL);
    std::string data_path_str = config.value("data_path", "");

    // Check for umamusume.exe
    std::filesystem::path data_path_fs(data_path_str);
    std::filesystem::path game_exe_path = data_path_fs.parent_path().parent_path() / "umamusume.exe";
    if (std::filesystem::exists(game_exe_path)) {
        std::cout << "游戏文件路径检测通过" << std::endl;
    } else {
        std::cout << "游戏文件路径错误: " << game_exe_path.string() << std::endl;
        // In Python it exits, but user might want to debug, but let's follow Python
        return 1;
    }

    // Load meta.json
    json meta = load_json_from_file(JSON_FILE);
    if (meta.is_null()) {
        return 1; // Error loading meta.json
    }

    if (!meta.is_array()) {
        std::cerr << "Error: meta.json is not a JSON array." << std::endl;
        return 1;
    }

    long long total_files = meta.size();
    std::cout << "元数据共 " << total_files << " 条, 加载成功" << std::endl;

    // User inputs
    long long start_index = last_index;
    std::cout << "请输入你要解密的文件起始索引 (默认是 " << last_index << "): ";
    std::string input_str;
    std::getline(std::cin, input_str);
    if (!input_str.empty()) {
        try {
            start_index = std::stoll(input_str);
        } catch (...) {}
    }

    long long limit = 0;
    std::cout << "请输入你要解密的文件数量 (输入 0 代表解密所有文件): ";
    std::getline(std::cin, input_str);
    if (!input_str.empty()) {
        try {
            limit = std::stoll(input_str);
        } catch (...) {}
    }
    if (limit == 0) {
        limit = total_files - start_index + 1; // Adjust limit if 0
    }

    long long output_interval = 1000;
    std::cout << "请输入调试信息输出间隔 (默认是 1000): ";
    std::getline(std::cin, input_str);
    if (!input_str.empty()) {
        try {
            output_interval = std::stoll(input_str);
        } catch (...) {}
    }

    // Decryption loop
    auto start_time = std::chrono::steady_clock::now();
    long long cnt = 0;
    long long continue_cnt = 0;

    for (size_t i = start_index; i < meta.size(); ++i) {
        const auto& entry = meta[i];
        
        // Extract information
        std::string entry_path = entry.value("path", "");
        std::string entry_url = entry.value("url", "");
        
        std::string final_key_for_decrypt_ab;
        json key_json_val = entry.value("key", json());

        if (key_json_val.is_string()) {
            final_key_for_decrypt_ab = key_json_val.get<std::string>();
        } else if (key_json_val.is_number_integer()) {
            long long key_val_as_int = key_json_val.get<long long>();
            if (key_val_as_int != 0) {
                std::vector<unsigned char> final_key_bytes = get_final_key(key_val_as_int);
                final_key_for_decrypt_ab = bytes_to_hex_string(final_key_bytes);
            }
        }

        bool continue_flag = false;

        // Handle path prefix "//"
        if (entry_path.rfind("//", 0) == 0) {
            entry_path = "0/" + entry_path.substr(2);
        }

        // Construct paths
        std::filesystem::path input_path_rel = join_paths("dat", entry_url.substr(0, 2));
        input_path_rel = join_paths(input_path_rel, entry_url);
        
        std::filesystem::path full_input_path = std::filesystem::path(data_path_str).make_preferred() / input_path_rel;

        if (!std::filesystem::exists(full_input_path)) {
            std::cout << "源文件不存在: \"" << full_input_path.string() << "\", 跳过解密" << std::endl;
            continue_cnt++;
            continue_flag = true;
        }

        std::filesystem::path output_path = join_paths("dat", entry_path);
        output_path.make_preferred();

        if (!continue_flag) {
            // Check existing file if strategy is "1" (skip existing)
            // Note: Python code uses DEC_STRATEGY == "1" to skip.
            // config.json uses "decryption_strategy".
            // If decryption_strategy is "1" (from Python input prompt logic) it means skip.
            // If it is "2", we don't skip.
            // Let's assume standard behavior: if file exists and we want to skip, we skip.
            if (std::filesystem::exists(output_path)) {
                if (decryption_strategy == "1") {
                    continue_cnt++;
                    continue_flag = true;
                }
            }
        }

        if (!continue_flag) {
            // Create directory
            std::error_code ec;
            std::filesystem::create_directories(output_path.parent_path(), ec);
            if (ec) {
                std::cerr << "Error: Could not create output directory for " << output_path.string() << std::endl;
                // Don't continue here, try to write anyway? No, fail.
                continue; // Or handle error
            }

            // Decrypt
            std::vector<unsigned char> decrypted_data = decrypt_ab(full_input_path, final_key_for_decrypt_ab);
            
            // Write
            std::ofstream output_file(output_path, std::ios::binary);
            if (output_file.is_open()) {
                output_file.write(reinterpret_cast<const char*>(decrypted_data.data()), decrypted_data.size());
                output_file.close();
            } else {
                 std::cerr << "Error: Could not write to " << output_path.string() << std::endl;
            }
        }

        cnt++;

        if (cnt % output_interval == 0 || cnt == limit) {
            auto current_time = std::chrono::steady_clock::now();
            std::chrono::duration<double> elapsed_seconds = current_time - start_time;
            double elapsed_time = elapsed_seconds.count();
            
            double avg_time_per_file = 0;
            double remaining_time = 0;
            long long remaining_files = limit - cnt;

            if (cnt > 0) {
                avg_time_per_file = elapsed_time / cnt;
                remaining_time = avg_time_per_file * remaining_files;
            }

            // Print status
            // Format: (cnt/limit) 源文件:"{ab_path}" 解密成功, 已保存为"{output_path}", 跳过{continue_cnt}个文件
            // Note: Python prints the path of the *last processed* file.
            std::cout << "(" << cnt << "/" << limit << ") " 
                      << "源文件:\"" << full_input_path.string() << "\" 解密成功, "
                      << "已保存为\"" << output_path.string() << "\", "
                      << "跳过" << continue_cnt << "个文件" << std::endl;

            // Format: 已用时间: {elapsed_time:.2f} 秒, 预计剩余时间: {remaining_time:.2f} 秒
            std::cout << std::fixed << std::setprecision(2);
            std::cout << "已用时间: " << elapsed_time << " 秒, "
                      << "预计剩余时间: " << remaining_time << " 秒" << std::endl;
            
            continue_cnt = 0; // Reset skipped counter

            // Update config
            config["last_index"] = start_index + cnt;
            std::ofstream config_file(CONFIG_FILE);
            if (config_file.is_open()) {
                config_file << std::setw(4) << config << std::endl;
            }
        }

        if (cnt >= limit) {
            break;
        }
    }

    std::cout << "解密完成" << std::endl;
    return 0;
}