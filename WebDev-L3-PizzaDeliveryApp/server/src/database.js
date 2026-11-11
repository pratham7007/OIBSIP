import mongoose from 'mongoose';
import bcrypt from 'bcryptjs';

const userSchema = new mongoose.Schema({
  name: { type: String, trim: true, maxlength: 80, default: '' },
  email: { type: String, required: true, unique: true, lowercase: true, trim: true },
  passwordHash: { type: String, required: true },
  role: { type: String, enum: ['user', 'admin'], default: 'user' },
  verifiedAt: { type: Date, default: null },
  verificationTokenHash: { type: String, default: null },
  verificationExpiresAt: { type: Date, default: null },
  resetTokenHash: { type: String, default: null },
  resetExpiresAt: { type: Date, default: null }
}, { timestamps: true });

const inventorySchema = new mongoose.Schema({
  key: { type: String, required: true, unique: true },
  category: { type: String, enum: ['base', 'sauce', 'cheese', 'vegetable'], required: true },
  name: { type: String, required: true },
  stock: { type: Number, min: 0, required: true },
  threshold: { type: Number, min: 0, default: 20 },
  lowStockNotified: { type: Boolean, default: false }
}, { timestamps: true });

const orderSchema = new mongoose.Schema({
  user: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  customerEmail: { type: String, required: true },
  pizzaName: { type: String, required: true },
  customization: {
    base: { type: String, required: true },
    sauce: { type: String, required: true },
    cheese: { type: String, required: true },
    vegetables: [{ type: String }]
  },
  inventoryKeys: [{ type: String }],
  amount: { type: Number, min: 1, required: true },
  currency: { type: String, default: 'INR' },
  paymentStatus: { type: String, enum: ['pending', 'processing', 'paid', 'failed'], default: 'pending' },
  paymentOrderId: { type: String, default: null },
  paymentId: { type: String, default: null },
  status: { type: String, enum: ['Order Received', 'In Kitchen', 'Sent to Delivery', 'Delivered'], default: 'Order Received' },
  inventoryCommittedAt: { type: Date, default: null }
}, { timestamps: true });

export const User = mongoose.model('User', userSchema);
export const Inventory = mongoose.model('Inventory', inventorySchema);
export const Order = mongoose.model('Order', orderSchema);

export const inventorySeed = [
  ['base-thin', 'base', 'Thin crust', 85], ['base-classic', 'base', 'Classic crust', 120],
  ['base-pan', 'base', 'Pan crust', 90], ['base-wholewheat', 'base', 'Whole wheat crust', 70],
  ['base-glutenfree', 'base', 'Gluten-free crust', 45],
  ['sauce-tomato', 'sauce', 'Roasted tomato', 140], ['sauce-pesto', 'sauce', 'Basil pesto', 55],
  ['sauce-bbq', 'sauce', 'Smoky BBQ', 75], ['sauce-white', 'sauce', 'Garlic cream', 60],
  ['sauce-spicy', 'sauce', 'Spicy arrabbiata', 65],
  ['cheese-mozzarella', 'cheese', 'Mozzarella', 160], ['cheese-vegan', 'cheese', 'Plant-based', 50],
  ['cheese-smoked', 'cheese', 'Smoked cheese', 60],
  ['veg-mushroom', 'vegetable', 'Mushrooms', 100], ['veg-pepper', 'vegetable', 'Bell peppers', 100],
  ['veg-onion', 'vegetable', 'Red onion', 100], ['veg-olive', 'vegetable', 'Olives', 80],
  ['veg-spinach', 'vegetable', 'Baby spinach', 70], ['veg-tomato', 'vegetable', 'Cherry tomatoes', 90]
].map(([key, category, name, stock]) => ({ key, category, name, stock, threshold: 20 }));

export async function connectDatabase(uri, adminEmail, adminPassword) {
  await mongoose.connect(uri);
  await Promise.all(inventorySeed.map((item) =>
    Inventory.updateOne({ key: item.key }, { $setOnInsert: item }, { upsert: true })
  ));

  if (adminEmail && adminPassword) {
    const email = adminEmail.trim().toLowerCase();
    const passwordHash = await bcrypt.hash(adminPassword, 12);
    await User.updateOne(
      { email },
      {
        $set: { passwordHash, role: 'admin', verifiedAt: new Date(), name: 'Store Admin' },
        $setOnInsert: { email }
      },
      { upsert: true }
    );
  }
  return mongoose.connection;
}
