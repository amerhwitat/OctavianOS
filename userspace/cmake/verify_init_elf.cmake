if(NOT DEFINED INIT_BINARY OR NOT EXISTS "${INIT_BINARY}")
    message(FATAL_ERROR "INIT_BINARY does not exist: ${INIT_BINARY}")
endif()

find_program(READELF_EXECUTABLE readelf)
if(NOT READELF_EXECUTABLE)
    message(FATAL_ERROR "readelf is required for static init ELF validation")
endif()

execute_process(
    COMMAND "${READELF_EXECUTABLE}" -h "${INIT_BINARY}"
    RESULT_VARIABLE header_rc
    OUTPUT_VARIABLE header
    ERROR_VARIABLE header_err
)
if(NOT header_rc EQUAL 0)
    message(FATAL_ERROR "readelf -h failed: ${header_err}")
endif()
if(NOT header MATCHES "Type:[ \t]+DYN")
    message(FATAL_ERROR "init must be a position-independent static PIE (ELF type DYN)")
endif()
if(header MATCHES "Entry point address:[ \t]+0x0([ \t\n]|$)")
    message(FATAL_ERROR "init ELF entry point is zero")
endif()

execute_process(
    COMMAND "${READELF_EXECUTABLE}" -l "${INIT_BINARY}"
    RESULT_VARIABLE program_rc
    OUTPUT_VARIABLE program_headers
    ERROR_VARIABLE program_err
)
if(NOT program_rc EQUAL 0)
    message(FATAL_ERROR "readelf -l failed: ${program_err}")
endif()
if(program_headers MATCHES "INTERP")
    message(FATAL_ERROR "static init ELF unexpectedly requests a dynamic interpreter")
endif()

execute_process(
    COMMAND "${READELF_EXECUTABLE}" -d "${INIT_BINARY}"
    RESULT_VARIABLE dynamic_rc
    OUTPUT_VARIABLE dynamic_section
    ERROR_VARIABLE dynamic_err
)
if(dynamic_rc EQUAL 0 AND dynamic_section MATCHES "\\(NEEDED\\)")
    message(FATAL_ERROR "static init ELF has a DT_NEEDED shared-library dependency")
endif()

message(STATUS "Static PIE init ELF contract passed: ${INIT_BINARY}")
