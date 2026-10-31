import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import time

# ==========================================
# 1. CONFIGURATION
# ==========================================

tf.keras.utils.set_random_seed(42)

EPOCHS = 15
BATCH_SIZE = 128

print("=" * 50)
print("MNIST V2 - CNN TRAINING")
print("=" * 50)

print("TensorFlow:", tf.__version__)
print("CPU threads:", tf.config.threading.get_inter_op_parallelism_threads())

# ==========================================
# 2. LOAD DATASET
# ==========================================

(x_train, y_train), (x_test, y_test) = (
    tf.keras.datasets.mnist.load_data()
)

# Normalize images
x_train = x_train.astype("float32") / 255.0
x_test = x_test.astype("float32") / 255.0

# Add channel dimension for CNN
x_train = np.expand_dims(x_train, axis=-1)
x_test = np.expand_dims(x_test, axis=-1)

print("Training shape:", x_train.shape)
print("Testing shape:", x_test.shape)

# ==========================================
# 3. DATA AUGMENTATION
# ==========================================

augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomRotation(0.05),
    tf.keras.layers.RandomTranslation(0.08, 0.08),
    tf.keras.layers.RandomZoom(0.05),
], name="augmentation")

# ==========================================
# 4. BUILD CNN
# ==========================================

model = tf.keras.Sequential([

    tf.keras.layers.Input(shape=(28, 28, 1)),

    # Data augmentation (active during training)
    augmentation,

    # First convolution block
    tf.keras.layers.Conv2D(
        32,
        kernel_size=3,
        padding="same",
        activation="relu"
    ),

    tf.keras.layers.MaxPooling2D(pool_size=2),

    # Second convolution block
    tf.keras.layers.Conv2D(
        64,
        kernel_size=3,
        padding="same",
        activation="relu"
    ),

    tf.keras.layers.MaxPooling2D(pool_size=2),

    # Classification layers
    tf.keras.layers.Flatten(),

    tf.keras.layers.Dense(
        128,
        activation="relu"
    ),

    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.Dense(
        10,
        activation="softmax"
    )
])

# ==========================================
# 5. COMPILE MODEL
# ==========================================

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# ==========================================
# 6. TRAINING CALLBACKS
# ==========================================

callbacks = [

    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=4,
        restore_best_weights=True
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=2,
        min_lr=0.00001
    )
]

# ==========================================
# 7. TRAIN MODEL
# ==========================================

print("\nSTARTING CNN TRAINING!")

start_time = time.perf_counter()

history = model.fit(
    x_train,
    y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_split=0.1,
    callbacks=callbacks,
    verbose=1
)

training_time = time.perf_counter() - start_time

# ==========================================
# 8. EVALUATE
# ==========================================

test_loss, test_accuracy = model.evaluate(
    x_test,
    y_test,
    verbose=0
)

print("\n" + "=" * 50)
print("FINAL CNN RESULTS")
print("=" * 50)

print(f"Training time: {training_time:.2f}s")
print(f"Epochs completed: {len(history.history['loss'])}")
print(f"Training accuracy: {history.history['accuracy'][-1] * 100:.2f}%")
print(f"Validation accuracy (last epoch): {history.history['val_accuracy'][-1] * 100:.2f}%")
print(f"Test accuracy: {test_accuracy * 100:.2f}%")
print(f"Test loss: {test_loss:.4f}")

# ==========================================
# 9. COMPARE WITH BASELINE
# ==========================================

baseline_accuracy = 97.53
baseline_time = 10.27

improvement = test_accuracy * 100 - baseline_accuracy

print("\nBASELINE COMPARISON")
print("-" * 50)

print(f"Original accuracy: {baseline_accuracy:.2f}%")
print(f"CNN accuracy: {test_accuracy * 100:.2f}%")
print(f"Accuracy improvement: {improvement:+.2f} percentage points")

print(f"\nOriginal training time: {baseline_time:.2f}s")
print(f"CNN training time: {training_time:.2f}s")

# ==========================================
# 10. SAVE MODEL
# ==========================================

model.save("mnist_cnn.keras")

print("\nCNN saved as mnist_cnn.keras")

# ==========================================
# 11. VISUALIZE RESULTS
# ==========================================

epochs_range = range(
    1,
    len(history.history["accuracy"]) + 1
)

plt.figure(figsize=(10, 5))

plt.plot(
    epochs_range,
    history.history["accuracy"],
    label="Training"
)

plt.plot(
    epochs_range,
    history.history["val_accuracy"],
    label="Validation"
)

plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.title("MNIST CNN Accuracy")
plt.legend()
plt.grid(True)

plt.savefig("cnn_accuracy.png")
plt.show()

plt.figure(figsize=(10, 5))

plt.plot(
    epochs_range,
    history.history["loss"],
    label="Training"
)

plt.plot(
    epochs_range,
    history.history["val_loss"],
    label="Validation"
)

plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("MNIST CNN Loss")
plt.legend()
plt.grid(True)

plt.savefig("cnn_loss.png")
plt.show()

# ==========================================
# 12. DISPLAY PREDICTIONS
# ==========================================

predictions = model.predict(
    x_test[:10],
    verbose=0
)

plt.figure(figsize=(12, 5))

for i in range(10):

    plt.subplot(2, 5, i + 1)

    plt.imshow(
        x_test[i].squeeze(),
        cmap="gray"
    )

    predicted = np.argmax(predictions[i])
    actual = y_test[i]

    plt.title(
        f"Pred: {predicted}\nActual: {actual}"
    )

    plt.axis("off")

plt.tight_layout()
plt.savefig("cnn_predictions.png")
plt.show()

print("\nMNIST V2 COMPLETED!")