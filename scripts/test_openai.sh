#!/bin/bash
#
# Automated test script for Story Generator with OpenAI
#
# Usage: OPENAI_API_KEY=your-key ./scripts/test_openai.sh
#
# Prerequisites:
# - OpenAI API key set in environment
# - Flask app running (http://localhost:5000)
# - jq installed for JSON parsing (brew install jq)
# - config.json configured for OpenAI

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:5000"

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

print_warning() {
    echo -e "  ${YELLOW}⚠${NC} $1"
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

    # Check OpenAI API key
    if [ -z "$OPENAI_API_KEY" ]; then
        print_fail "OPENAI_API_KEY environment variable not set"
        print_info "Set it with: export OPENAI_API_KEY=your-key"
        exit 1
    fi
    print_pass "OPENAI_API_KEY is set"
    print_warning "Note: OpenAI API calls will incur costs"

    # Check Flask app
    if ! curl -s "${BASE_URL}/health" &> /dev/null; then
        print_fail "Flask app not running at ${BASE_URL}"
        print_info "Start the app with: python -m src.app"
        exit 1
    fi
    print_pass "Flask app is running"

    # Verify configuration is set to OpenAI
    CONFIG=$(curl -s "${BASE_URL}/api/config")
    PROVIDER=$(echo $CONFIG | jq -r '.ai_providers.text_provider')

    if [ "$PROVIDER" != "openai" ]; then
        print_fail "App is not configured for OpenAI (current: $PROVIDER)"
        print_info "Update config.json to use OpenAI as text_provider"
        exit 1
    fi
    print_pass "App configured for OpenAI"
}

# Test 1: Health check
test_health() {
    print_test 1 "Health check endpoint"

    RESPONSE=$(curl -s "${BASE_URL}/health")
    STATUS=$(echo $RESPONSE | jq -r '.status')

    if [ "$STATUS" = "healthy" ]; then
        print_pass "Health endpoint returns healthy status"
    else
        print_fail "Health endpoint returned: $STATUS"
    fi
}

# Test 2: Simple story generation with OpenAI
test_simple_story() {
    print_test 2 "Simple story generation with OpenAI"

    print_info "Generating 3-page story (this may take 10-20 seconds)..."

    START_TIME=$(date +%s)

    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "The Clever Fox",
            "num_pages": 3,
            "age_group": "3-5",
            "complexity": "simple"
        }')

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Check if response is valid JSON
    if ! echo "$RESPONSE" | jq empty 2>/dev/null; then
        print_fail "Invalid JSON response"
        print_info "Response: ${RESPONSE:0:200}..."
        return
    fi

    # Check for error in response
    ERROR=$(echo $RESPONSE | jq -r '.error // empty')
    if [ -n "$ERROR" ]; then
        print_fail "Story generation failed: $ERROR"
        return
    fi

    STORY_ID=$(echo $RESPONSE | jq -r '.id')
    NUM_PAGES=$(echo $RESPONSE | jq '.pages | length')
    TITLE=$(echo $RESPONSE | jq -r '.metadata.title')

    if [ -n "$STORY_ID" ] && [ "$STORY_ID" != "null" ]; then
        print_pass "Story created successfully"
        print_info "Response time: ${DURATION}s"
        print_info "Story ID: $STORY_ID"
        print_info "Title: $TITLE"
        print_info "Pages: $NUM_PAGES"

        if [ "$NUM_PAGES" = "3" ]; then
            print_pass "Story has correct number of pages"
        else
            print_fail "Expected 3 pages, got $NUM_PAGES"
        fi

        # Check quality indicators
        FIRST_PAGE=$(echo $RESPONSE | jq -r '.pages[0].text')
        WORD_COUNT=$(echo "$FIRST_PAGE" | wc -w | tr -d ' ')

        print_info "First page word count: $WORD_COUNT"

        if [ "$WORD_COUNT" -gt 20 ]; then
            print_pass "Story has substantial content"
        else
            print_warning "Story may be too short"
        fi

        # Save for later tests
        export TEST_STORY_ID=$STORY_ID
        export TEST_STORY_RESPONSE=$RESPONSE
    else
        print_fail "Story creation failed"
        print_info "Response: ${RESPONSE:0:200}..."
    fi
}

# Test 3: Quality check with OpenAI
test_story_quality() {
    print_test 3 "Story quality with GPT-3.5"

    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "The Magical Garden",
            "num_pages": 3,
            "theme": "nature and discovery",
            "age_group": "3-5",
            "complexity": "simple",
            "genre": "fantasy"
        }')

    ERROR=$(echo $RESPONSE | jq -r '.error // empty')
    if [ -n "$ERROR" ]; then
        print_fail "Story generation failed: $ERROR"
        return
    fi

    # Extract full story text
    FULL_TEXT=$(echo $RESPONSE | jq -r '.pages[].text' | tr '\n' ' ')

    # Quality checks
    TOTAL_WORDS=$(echo "$FULL_TEXT" | wc -w | tr -d ' ')
    print_info "Total story length: $TOTAL_WORDS words"

    # Check for theme incorporation
    if echo "$FULL_TEXT" | grep -iq "garden\|plant\|flower\|nature"; then
        print_pass "Theme appears incorporated in story"
    else
        print_warning "Theme may not be clearly incorporated"
    fi

    # Check for age-appropriate language (simple words)
    if echo "$FULL_TEXT" | grep -Eq "[A-Za-z]{12,}"; then
        print_warning "Story may contain complex words for age 3-5"
    else
        print_pass "Language appears age-appropriate"
    fi

    # Check character extraction with OpenAI
    NUM_CHARACTERS=$(echo $RESPONSE | jq '.characters | length')
    if [ "$NUM_CHARACTERS" -gt 0 ]; then
        print_pass "Characters extracted: $NUM_CHARACTERS"
        echo $RESPONSE | jq -r '.characters[] | "  - \(.name): \(.physical_description // "no description")"'
    else
        print_info "No characters extracted"
    fi
}

# Test 4: Custom prompt creativity
test_custom_prompt() {
    print_test 4 "Custom prompt with OpenAI creativity"

    RESPONSE=$(curl -s -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "The Time-Traveling Teddy Bear",
            "num_pages": 5,
            "custom_prompt": "A teddy bear discovers a magical clock that allows it to travel through different historical eras, learning about different cultures"
        }')

    ERROR=$(echo $RESPONSE | jq -r '.error // empty')
    if [ -n "$ERROR" ]; then
        print_fail "Story generation failed: $ERROR"
        return
    fi

    STORY_ID=$(echo $RESPONSE | jq -r '.id')
    if [ -n "$STORY_ID" ] && [ "$STORY_ID" != "null" ]; then
        print_pass "Complex custom prompt story created"

        FULL_TEXT=$(echo $RESPONSE | jq -r '.pages[].text' | tr '\n' ' ')

        # Check for custom prompt elements
        if echo "$FULL_TEXT" | grep -iq "teddy\|bear"; then
            print_pass "Main character (teddy bear) is present"
        else
            print_fail "Main character missing from story"
        fi

        if echo "$FULL_TEXT" | grep -iq "time\|travel\|clock\|past\|history"; then
            print_pass "Time travel theme is present"
        else
            print_warning "Time travel theme may not be clearly incorporated"
        fi

        NUM_PAGES=$(echo $RESPONSE | jq '.pages | length')
        if [ "$NUM_PAGES" = "5" ]; then
            print_pass "Story has requested 5 pages"
        else
            print_warning "Expected 5 pages, got $NUM_PAGES"
        fi
    else
        print_fail "Custom prompt story creation failed"
    fi
}

# Test 5: Performance comparison
test_performance() {
    print_test 5 "Performance metrics"

    print_info "Testing different story lengths..."

    # Test 3-page story
    START=$(date +%s)
    curl -s -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{"title": "Short Test", "num_pages": 3}' > /dev/null
    END=$(date +%s)
    TIME_3=$(($END - $START))
    print_info "3 pages: ${TIME_3}s"

    # Test 5-page story
    START=$(date +%s)
    curl -s -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{"title": "Medium Test", "num_pages": 5}' > /dev/null
    END=$(date +%s)
    TIME_5=$(($END - $START))
    print_info "5 pages: ${TIME_5}s"

    if [ $TIME_3 -lt 30 ] && [ $TIME_5 -lt 50 ]; then
        print_pass "Performance is within acceptable range"
    else
        print_warning "Performance may be slower than expected"
    fi

    # Estimate cost (rough estimate)
    # GPT-3.5-turbo: ~$0.002 per 1K tokens
    # Average story ~2K tokens output + 500 input = 2.5K tokens = $0.005
    print_info "Estimated cost per story: ~\$0.005-0.01"
}

# Test 6: Error handling with API issues
test_error_handling() {
    print_test 6 "Error handling"

    # Test missing title
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d '{"num_pages": 3}')

    if [ "$HTTP_STATUS" = "400" ]; then
        print_pass "Missing field returns 400"
    else
        print_fail "Expected 400, got $HTTP_STATUS"
    fi

    # Test invalid JSON
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/stories" \
        -H "Content-Type: application/json" \
        -d 'invalid json')

    if [ "$HTTP_STATUS" = "400" ]; then
        print_pass "Invalid JSON returns 400"
    else
        print_fail "Expected 400, got $HTTP_STATUS"
    fi
}

# Main execution
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Story Generator - OpenAI Test Suite${NC}"
    echo -e "${GREEN}========================================${NC}"

    check_prerequisites
    test_health
    test_simple_story
    test_story_quality
    test_custom_prompt
    test_performance
    test_error_handling

    # Print summary
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Test Summary${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "Total tests run: ${TESTS_RUN}"
    echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"

    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
        echo -e "\n${YELLOW}Note: Some failures may be due to API rate limits or network issues${NC}"
        exit 1
    else
        echo -e "Failed: 0"
        echo -e "\n${GREEN}✓ All tests passed!${NC}"
        echo -e "\n${YELLOW}Note: API calls incurred costs. Check your OpenAI dashboard.${NC}"
        exit 0
    fi
}

# Run tests
main
