// ============================================================
// MongoDB $lookup Queries — JOIN equivalents
// ============================================================

db = db.getSiblingDB("ecommerce_nosql");

// ──────────────────────────────────────────────────────────
// 1. Order with user details ($lookup — equivalent to JOIN)
// ──────────────────────────────────────────────────────────
// NOTE: In most cases you DON'T need this because orders already
// embed item snapshots. This demonstrates $lookup for comparison.
db.orders.aggregate([
  { $match: { _id: ObjectId("000000000000000000000004") } },
  {
    $lookup: {
      from: "users",
      localField: "userId",
      foreignField: "_id",
      as: "user"
    }
  },
  { $unwind: "$user" },
  {
    $project: {
      orderId: "$_id",
      orderDate: "$createdAt",
      status: 1,
      totalAmount: 1,
      "customer.name":  "$user.fullName",
      "customer.email": "$user.email",
      items: 1,
      shippingAddress: 1
    }
  }
]);

// ──────────────────────────────────────────────────────────
// 2. Products with category name (resolve FK reference)
// ──────────────────────────────────────────────────────────
db.products.aggregate([
  { $match: { isActive: true } },
  {
    $lookup: {
      from: "categories",
      localField: "categoryId",
      foreignField: "_id",
      as: "category"
    }
  },
  { $unwind: "$category" },
  {
    $project: {
      name: 1,
      price: 1,
      stock: 1,
      brand: 1,
      categoryName: "$category.name",
      ratingSummary: 1
    }
  },
  { $sort: { "ratingSummary.avgRating": -1 } },
  { $limit: 20 }
]);

// ──────────────────────────────────────────────────────────
// 3. Users who have never placed an order
// (equivalent to LEFT JOIN ... WHERE order_id IS NULL)
// ──────────────────────────────────────────────────────────
db.users.aggregate([
  {
    $lookup: {
      from: "orders",
      localField: "_id",
      foreignField: "userId",
      as: "orders"
    }
  },
  // Filter: no orders
  { $match: { orders: { $size: 0 }, isActive: true } },
  {
    $project: {
      email: 1,
      username: 1,
      createdAt: 1
    }
  },
  { $sort: { createdAt: -1 } }
]);

// ──────────────────────────────────────────────────────────
// 4. Products frequently bought together
// (self-join on orders — equivalent to SQL cross-join trick)
// ──────────────────────────────────────────────────────────
db.orders.aggregate([
  { $match: { status: { $nin: ["cancelled", "refunded"] } } },
  // Create pairs of items within same order
  {
    $project: {
      pairs: {
        $reduce: {
          input: "$items",
          initialValue: { result: [], visited: [] },
          in: {
            result: {
              $concatArrays: [
                "$$value.result",
                {
                  $map: {
                    input: "$$value.visited",
                    as: "prev",
                    in: {
                      a: "$$prev.productId",
                      b: "$$this.productId",
                      nameA: "$$prev.productName",
                      nameB: "$$this.productName"
                    }
                  }
                }
              ]
            },
            visited: { $concatArrays: ["$$value.visited", ["$$this"]] }
          }
        }
      }
    }
  },
  { $unwind: "$pairs.result" },
  {
    $group: {
      _id: { a: "$pairs.result.a", b: "$pairs.result.b" },
      productA: { $first: "$pairs.result.nameA" },
      productB: { $first: "$pairs.result.nameB" },
      coPurchaseCount: { $sum: 1 }
    }
  },
  { $sort: { coPurchaseCount: -1 } },
  { $limit: 20 }
]);
