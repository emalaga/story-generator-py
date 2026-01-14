#!/bin/bash
#
# Automated test script for Story Generator with Ollama
#
# Usage: ./scripts/test_ollama.sh
#
# Prerequisites:
# - Ollama installed and running (http://localhost:11434)
# - Flask app running (http://localhost:5000)
# - jq installed for JSON parsing (brew install jq)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:5000"
OLLAMA_URL="http://localhost:11434"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_test() {
    echo -e "\n${YELLOW}▶ Test $1: $2${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))
}

print_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

print_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

print_info() {
    echo -e "  ℹ $1"
}

# Check prerequisites
check_prerequisites() {
    print_test 0 "Checking prerequisites"

    # Check jq
    if ! command -v jq &> /dev/null; then
        print_fail "jq not found. Install with: brew install jq"
        exit 1
    fi
    print_pass "jq is installed"

    # Check Ollama
    if ! curl -s "${OLLAMA_URL}/api/tags" &> /dev/null; then
        print_fail "Ollama not running at ${OLLAMA_URL}"
        print_info "Start Ollama and try again"
        exit 1
    fi
    print_pass "Ollama is running"

    # Check Flask app
    if ! curl -s "${BASE_URL}/health" &> /dev/null; then
        print_fail "Flask app not running at ${BASE_URL}"
        print_info "Start the app with: python -m src.app"
        exit 1
    fi
    print_pass "Flask app is running"
}

# Test 1: Health check
test_health() {
    print_test 1 "Health check endpoint"

    RESPONSE=$(curl -s "${BASE_URL}/health")
    STATUS=$(echo $RESPONSE | jq -r '.status')

    if [ "$STATUS" = "healthy" ]; then
        print_pass "Health endpoint returns healthy status"
        print_info "Response: $RESPONSE"
    else
        print_fail "Health endpoint returned: $STATUS"
    fi
}

# Test 2: Configuration
test_config() {
    print_test 2 "Configuration endpoint"

    RESPONSE=$(curl -s "${BASE_URL}/api/config")

    # Check if response contains expected fields
    if echo $RESPONSE | jq -e '.parameters' &> /dev/null && \
       echo $RESPONSE | jq -e '.defaults' &> /dev/null && \
       echo $RESPONSE | jq -e '.ai_providers' &> /dev/null; then
        print_pass "Configuration has all required fields"

        PROVIDER=$(echo $RESPONSE | jq -r '.ai_providers.text_provider')
        print_info "Text provider: $PROVIDER"

        # Check that API keys are not exposed
        if echo $RESPONSE | grep -q "api_key"; then
            print_fail "API keys are exposed in configuration!"
        else
            print_pass "API keys are properly hidden"
        fi
    else
        print_fail "Configuration missing required fields"
    fi
}

# Test 3: Simple story generation
test_simple_story() {
    print_test 3 "Simple story generation (3 pages)"

    START_TIME=$(date +%s)

    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "The Brave Little Mouse",
            "num_pages": 3
        }')

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Check HTTP status
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{"title": "Test", "num_pages": 3}')

    if [ "$HTTP_STATUS" = "201" ]; then
        print_pass "Story created successfully (HTTP 201)"
        print_info "Response time: ${DURATION}s"

        # Validate response structure
        STORY_ID=$(echo $RESPONSE | jq -r '.id')
        NUM_PAGES=$(echo $RESPONSE | jq '.pages | length')
        TITLE=$(echo $RESPONSE | jq -r '.metadata.title')

        print_info "Story ID: $STORY_ID"
        print_info "Title: $TITLE"
        print_info "Pages: $NUM_PAGES"

        if [ "$NUM_PAGES" = "3" ]; then
            print_pass "Story has correct number of pages"
        else
            print_fail "Expected 3 pages, got $NUM_PAGES"
        fi

        # Check first page content
        FIRST_PAGE=$(echo $RESPONSE | jq -r '.pages[0].text')
        if [ -n "$FIRST_PAGE" ] && [ "$FIRST_PAGE" != "null" ]; then
            print_pass "Story has content"
            print_info "First page preview: ${FIRST_PAGE:0:80}..."
        else
            print_fail "Story pages are empty"
        fi

        # Save story ID for later tests
        export TEST_STORY_ID=$STORY_ID
        export TEST_STORY_RESPONSE=$RESPONSE
    else
        print_fail "Story creation failed (HTTP $HTTP_STATUS)"
        print_info "Response: $RESPONSE"
    fi
}

# Test 4: Story with theme
test_story_with_theme() {
    print_test 4 "Story with theme"

    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Friends Forever",
            "num_pages": 3,
            "theme": "friendship and kindness",
            "age_group": "3-5",
            "complexity": "simple"
        }')

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{"title": "Friends Forever", "num_pages": 3, "theme": "friendship"}')

    if [ "$HTTP_STATUS" = "201" ]; then
        print_pass "Themed story created successfully"

        # Check if theme is reflected in story
        FULL_TEXT=$(echo $RESPONSE | jq -r '.pages[].text' | tr '\n' ' ')
        if echo "$FULL_TEXT" | grep -iq "friend"; then
            print_pass "Theme appears to be incorporated in story"
        else
            print_info "Theme may not be clearly incorporated (manual review recommended)"
        fi
    else
        print_fail "Themed story creation failed"
    fi
}

# Test 5: Story with custom prompt
test_custom_prompt() {
    print_test 5 "Story with custom prompt"

    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "The Reading Dragon",
            "num_pages": 3,
            "custom_prompt": "A story about a dragon who discovers the joy of reading books"
        }')

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{"title": "Test", "num_pages": 3, "custom_prompt": "test"}')

    if [ "$HTTP_STATUS" = "201" ]; then
        print_pass "Custom prompt story created successfully"

        FULL_TEXT=$(echo $RESPONSE | jq -r '.pages[].text' | tr '\n' ' ')
        if echo "$FULL_TEXT" | grep -iq "dragon" && echo "$FULL_TEXT" | grep -iq "read"; then
            print_pass "Custom prompt elements found in story"
        else
            print_info "Custom prompt may not be fully incorporated"
        fi
    else
        print_fail "Custom prompt story creation failed"
    fi
}

# Test 6: Character extraction
test_character_extraction() {
    print_test 6 "Character extraction"

    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "The Forest Adventure",
            "num_pages": 3,
            "theme": "A brave fox named Felix explores the forest"
        }')

    NUM_CHARACTERS=$(echo $RESPONSE | jq '.characters | length')

    if [ "$NUM_CHARACTERS" -gt 0 ]; then
        print_pass "Characters extracted: $NUM_CHARACTERS"

        # Show character details
        echo $RESPONSE | jq -r '.characters[] | "  - \(.name) (\(.species // "unknown")): \(.physical_description // "no description")"'
    else
        print_info "No characters extracted (may be normal for some stories)"
    fi
}

# Test 7: Single page image generation
test_image_generation() {
    print_test 7 "Single page image generation"

    if [ -z "$TEST_STORY_ID" ]; then
        print_fail "No story ID available (previous test may have failed)"
        return
    fi

    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/images/stories/${TEST_STORY_ID}/pages/1" \
        -H "Content-Type: application/json" \
        -d '{
            "scene_description": "A brave little mouse exploring a colorful garden",
            "art_style": "cartoon"
        }')

    IMAGE_URL=$(echo $RESPONSE | jq -r '.image_url')

    if [ -n "$IMAGE_URL" ] && [ "$IMAGE_URL" != "null" ]; then
        print_pass "Image generated successfully"
        print_info "Image URL: $IMAGE_URL"
    else
        print_fail "Image generation failed"
        print_info "Response: $RESPONSE"
    fi
}

# Test 8: Project creation
test_project_creation() {
    print_test 8 "Project creation and retrieval"

    if [ -z "$TEST_STORY_RESPONSE" ]; then
        print_fail "No story available (previous test may have failed)"
        return
    fi

    # Create project
    PROJECT_DATA=$(cat <<EOF
{
    "id": "$TEST_STORY_ID",
    "name": "Test Project",
    "story": $TEST_STORY_RESPONSE,
    "status": "completed",
    "character_profiles": [],
    "image_prompts": []
}
EOF
)

    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/projects" \
        -H "Content-Type: application/json" \
        -d "$PROJECT_DATA")

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/projects" \
        -H "Content-Type: application/json" \
        -d "$PROJECT_DATA")

    if [ "$HTTP_STATUS" = "201" ]; then
        print_pass "Project created successfully"

        # List projects
        PROJECTS=$(curl -s "${BASE_URL}/api/projects")
        if echo "$PROJECTS" | jq -e ". | contains([\"$TEST_STORY_ID\"])" &> /dev/null; then
            print_pass "Project appears in project list"
        else
            print_fail "Project not found in list"
        fi

        # Retrieve project
        PROJECT=$(curl -s "${BASE_URL}/api/projects/${TEST_STORY_ID}")
        if echo "$PROJECT" | jq -e '.name' &> /dev/null; then
            print_pass "Project retrieved successfully"
        else
            print_fail "Project retrieval failed"
        fi

        # Delete project
        DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${BASE_URL}/api/projects/${TEST_STORY_ID}")
        if [ "$DELETE_STATUS" = "200" ] || [ "$DELETE_STATUS" = "204" ]; then
            print_pass "Project deleted successfully"
        else
            print_fail "Project deletion failed (HTTP $DELETE_STATUS)"
        fi
    else
        print_fail "Project creation failed (HTTP $HTTP_STATUS)"
    fi
}

# Test 9: Error handling
test_error_handling() {
    print_test 9 "Error handling"

    # Test missing required field
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{"num_pages": 3}')

    if [ "$HTTP_STATUS" = "400" ]; then
        print_pass "Missing field returns 400 Bad Request"
    else
        print_fail "Expected 400 for missing field, got $HTTP_STATUS"
    fi

    # Test invalid JSON
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d 'not valid json')

    if [ "$HTTP_STATUS" = "400" ]; then
        print_pass "Invalid JSON returns 400 Bad Request"
    else
        print_fail "Expected 400 for invalid JSON, got $HTTP_STATUS"
    fi

    # Test non-existent resource
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/stories/nonexistent-id-12345")

    if [ "$HTTP_STATUS" = "404" ]; then
        print_pass "Non-existent resource returns 404 Not Found"
    else
        print_fail "Expected 404 for non-existent resource, got $HTTP_STATUS"
    fi
}

# Main test execution
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Story Generator - Ollama Test Suite${NC}"
    echo -e "${GREEN}========================================${NC}"

    check_prerequisites
    test_health
    test_config
    test_simple_story
    test_story_with_theme
    test_custom_prompt
    test_character_extraction
    test_image_generation
    test_project_creation
    test_error_handling

    # Print summary
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Test Summary${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "Total tests run: ${TESTS_RUN}"
    echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"

    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
        exit 1
    else
        echo -e "Failed: 0"
        echo -e "\n${GREEN}✓ All tests passed!${NC}"
        exit 0
    fi
}

# Run tests
main
