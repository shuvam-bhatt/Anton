Okay, here is the content for a C++ file named `sort.cpp` that demonstrates how to sort an array of integers using the C++ Standard Library's `std::sort` function.

```cpp
// Filename: sort.cpp
// Description: A C++ program to sort an array of integers.

#include <iostream> // For input/output operations (cout)
#include <algorithm> // For the std::sort function
#include <vector>    // Using vector is often more flexible than raw arrays

// Function to print the elements of a vector
void printArray(const std::vector<int>& arr) {
    for (size_t i = 0; i < arr.size(); ++i) {
        std::cout << arr[i] << (i == arr.size() - 1 ? "" : ", "); // Print comma, except for the last element
    }
    std::cout << std::endl;
}

int main() {
    // 1. Define an array (using std::vector for modern C++ flexibility)
    // If you specifically need a C-style array, see comment below.
    std::vector<int> numbers = { 5, 2, 9, 1, 5, 6, 3, 8, 4, 7 };

    /*
    // Alternative: Using a C-style array
    int numbers_cstyle[] = { 5, 2, 9, 1, 5, 6, 3, 8, 4, 7 };
    // To use std::sort with a C-style array, you need its size:
    // size_t n = sizeof(numbers_cstyle) / sizeof(numbers_cstyle[0]);
    // std::sort(numbers_cstyle, numbers_cstyle + n);
    // You would need a different print function for C-style arrays.
    // For simplicity and modern practice, std::vector is used below.
    */

    // 2. Print the original array
    std::cout << "Original array: ";
    printArray(numbers);

    // 3. Sort the array in ascending order
    // std::sort takes two iterators: one to the beginning and one to the end
    // For a std::vector, begin() and end() provide these iterators.
    std::sort(numbers.begin(), numbers.end());

    // 4. Print the sorted array
    std::cout << "Sorted array (ascending): ";
    printArray(numbers);

    // Optional: Sort in descending order
    // std::sort can take a third parameter, a comparison function/object.
    // std::greater<int>() is a predefined object for descending order comparison.
    std::sort(numbers.begin(), numbers.end(), std::greater<int>());

    // 5. Print the array sorted in descending order
    std::cout << "Sorted array (descending): ";
    printArray(numbers);

    // Indicate successful execution
    return 0;
}
```

**Explanation:**

1.  **`#include <iostream>`:** Includes the standard input/output library, necessary for using `std::cout` to print to the console.
2.  **`#include <algorithm>`:** This is the crucial header file that contains the `std::sort` function.
3.  **`#include <vector>`:** Includes the `std::vector` container, a dynamic array that is often preferred over C-style arrays in modern C++ due to its flexibility and features. We use `std::vector` in this example.
4.  **`void printArray(const std::vector<int>& arr)`:** A helper function to neatly print the contents of the `std::vector`. It iterates through the elements and prints them separated by commas. `const&` is used for efficiency and to prevent modification of the original vector.
5.  **`int main() { ... }`:** The main function where program execution begins.
6.  **`std::vector<int> numbers = { ... };`:** Initializes a `std::vector` named `numbers` with a list of integers.
7.  **`printArray(numbers);`:** Calls the helper function to display the vector's contents before sorting.
8.  **`std::sort(numbers.begin(), numbers.end());`:** This is where the sorting happens.
    *   `std::sort` is a generic function that can sort elements in a range defined by two iterators.
    *   `numbers.begin()` returns an iterator pointing to the first element of the vector.
    *   `numbers.end()` returns an iterator pointing to the position *one past* the last element of the vector.
    *   `std::sort` sorts the elements in the range `[begin, end)` (inclusive of begin, exclusive of end). By default, it sorts in ascending order using the `<` operator for the element type.
9.  **`std::sort(numbers.begin(), numbers.end(), std::greater<int>());`:** This shows how to sort in descending order. The third argument, `std::greater<int>()`, is a function object that defines the comparison criterion (use `>` instead of `<`).
10. **`return 0;`:** Indicates that the program executed successfully.

**How to Compile and Run:**

1.  Save the code above in a file named `sort.cpp`.
2.  Open a terminal or command prompt.
3.  Navigate to the directory where you saved the file.
4.  Compile the code using a C++ compiler like g++:
    ```bash
    g++ sort.cpp -o sort -std=c++11
    ```
    *(`-std=c++11` or higher is recommended to use features like initializer lists `{}` for vectors)*
5.  Run the compiled program:
    ```bash
    ./sort
    ```

You will see output showing the array before sorting, after ascending sort, and after descending sort.