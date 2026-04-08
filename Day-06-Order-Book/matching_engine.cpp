#include <iostream>
#include <vector>
#include <map>
#include <list>
#include <string>
#include <chrono>
#include <iomanip>
#include <functional> // For std::greater

// Represents a single order in the book
struct Order {
    long long OrderID;
    bool IsBuy;
    double Price;
    int Quantity;
    long long Timestamp; // For time priority
};

// The main class for the Limit Order Book and Matching Engine
class OrderBook {
private:
    // Bids are buy orders, sorted from highest price to lowest (std::greater)
    // Key: Price, Value: List of orders at that price (for time priority)
    std::map<double, std::list<Order>, std::greater<double>> bids;

    // Asks are sell orders, sorted from lowest price to highest (default map behavior)
    std::map<double, std::list<Order>> asks;

    long long nextOrderID = 1;

    // Generates a unique timestamp (nanoseconds since epoch)
    long long getCurrentTimestamp() {
        return std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::high_resolution_clock::now().time_since_epoch()
        ).count();
    }

public:
    // Adds a new order to the book and triggers matching
    void addOrder(bool isBuy, double price, int quantity) {
        Order newOrder = {
            nextOrderID++,
            isBuy,
            price,
            quantity,
            getCurrentTimestamp()
        };

        if (isBuy) {
            bids[price].push_back(newOrder);
            std::cout << "--> ADDED BID: " << quantity << " @ " << price << std::endl;
        } else {
            asks[price].push_back(newOrder);
            std::cout << "--> ADDED ASK: " << quantity << " @ " << price << std::endl;
        }

        matchOrders();
    }

    // The core matching engine logic
    void matchOrders() {
        // Loop while there are orders on both sides and the best bid is >= best ask
        while (!bids.empty() && !asks.empty() && bids.begin()->first >= asks.begin()->first) {
            
            auto& bestBidPriceLevel = bids.begin()->second;
            auto& bestAskPriceLevel = asks.begin()->second;

            // Get the first order at each price level (time priority)
            Order& bestBidOrder = bestBidPriceLevel.front();
            Order& bestAskOrder = bestAskPriceLevel.front();

            // Determine trade quantity
            int tradeQuantity = std::min(bestBidOrder.Quantity, bestAskOrder.Quantity);

            std::cout << "\n*** MATCH FOUND! ***" << std::endl;
            std::cout << "   Executing trade of " << tradeQuantity << " shares at price " << asks.begin()->first << std::endl;
            std::cout << "   (Bid ID: " << bestBidOrder.OrderID << " vs Ask ID: " << bestAskOrder.OrderID << ")" << std::endl;

            // Update quantities
            bestBidOrder.Quantity -= tradeQuantity;
            bestAskOrder.Quantity -= tradeQuantity;

            // If an order is fully filled, remove it
            if (bestBidOrder.Quantity == 0) {
                bestBidPriceLevel.pop_front();
            }
            if (bestAskOrder.Quantity == 0) {
                bestAskPriceLevel.pop_front();
            }

            // If a price level is now empty, remove it from the book
            if (bestBidPriceLevel.empty()) {
                bids.erase(bids.begin());
            }
            if (bestAskPriceLevel.empty()) {
                asks.erase(asks.begin());
            }
            std::cout << "********************\n" << std::endl;
        }
    }

    // Prints the current state of the order book
    void printBook() const {
        std::cout << "\n==================== ORDER BOOK ====================" << std::endl;
        
        // Print Asks (sells) in reverse order (from highest price to lowest)
        std::cout << "----------- ASKS -----------" << std::endl;
        std::cout << std::setw(10) << "Price" << " | " << std::setw(10) << "Quantity" << std::endl;
        std::cout << "----------------------------" << std::endl;
        for (auto it = asks.rbegin(); it != asks.rend(); ++it) {
            int totalQuantity = 0;
            for (const auto& order : it->second) {
                totalQuantity += order.Quantity;
            }
            std::cout << std::setw(10) << std::fixed << std::setprecision(2) << it->first 
                      << " | " << std::setw(10) << totalQuantity << std::endl;
        }

        std::cout << "\n----------- SPREAD -----------\n" << std::endl;

        // Print Bids (buys) - already sorted high to low
        std::cout << "----------- BIDS -----------" << std::endl;
        std::cout << std::setw(10) << "Price" << " | " << std::setw(10) << "Quantity" << std::endl;
        std::cout << "----------------------------" << std::endl;
        for (const auto& pair : bids) {
            int totalQuantity = 0;
            for (const auto& order : pair.second) {
                totalQuantity += order.Quantity;
            }
            std::cout << std::setw(10) << std::fixed << std::setprecision(2) << pair.first 
                      << " | " << std::setw(10) << totalQuantity << std::endl;
        }
        std::cout << "==================================================\n" << std::endl;
    }
};

int main() {
    OrderBook book;

    std::cout << "--- Building initial order book ---" << std::endl;
    // Build up the ask side
    book.addOrder(false, 101.50, 100); // Sell 100 @ 101.50
    book.addOrder(false, 101.75, 50);  // Sell 50  @ 101.75
    book.addOrder(false, 101.50, 75);  // Sell 75  @ 101.50 (time priority after first)

    // Build up the bid side
    book.addOrder(true, 99.50, 200);   // Buy 200 @ 99.50
    book.addOrder(true, 99.25, 150);   // Buy 150 @ 99.25

    book.printBook();

    // --- Simulation 1: A buy order crosses the spread (partial fill) ---
    std::cout << "\n--- SIMULATION 1: Buyer crosses spread, partial fill ---" << std::endl;
    book.addOrder(true, 101.50, 120); // Buy 120 @ 101.50
    // This should match with the first sell order of 100 @ 101.50.
    // The remaining 20 of the buy order will not be filled yet.
    // The second sell order of 75 @ 101.50 will then be matched with the remaining 20.
    
    book.printBook();
    // Expected state:
    // Asks: 55 @ 101.50, 50 @ 101.75
    // Bids: 200 @ 99.50, 150 @ 99.25

    // --- Simulation 2: A sell order crosses the spread (full fill of a level) ---
    std::cout << "\n--- SIMULATION 2: Seller crosses spread, fills entire level ---" << std::endl;
    book.addOrder(false, 99.50, 200); // Sell 200 @ 99.50
    // This should match perfectly with the buy order of 200 @ 99.50, removing that price level.

    book.printBook();
    // Expected state:
    // Asks: 55 @ 101.50, 50 @ 101.75
    // Bids: 150 @ 99.25

    // --- Simulation 3: A large buy order sweeps multiple levels ---
    std::cout << "\n--- SIMULATION 3: Aggressive buyer sweeps two levels ---" << std::endl;
    book.addOrder(true, 102.00, 150); // Buy 150 @ 102.00
    // This aggressive buy order should fill:
    // 1. The remaining 55 @ 101.50
    // 2. The entire 50 @ 101.75
    // 3. The remaining 45 (150 - 55 - 50) will sit as the new best bid @ 102.00

    book.printBook();
    // Expected state:
    // Asks: (empty)
    // Bids: 45 @ 102.00, 150 @ 99.25

    return 0;
}