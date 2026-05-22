export class OpportunityQueue {
  #queue = [];

  enqueue(opportunity) {
    this.#queue.push(opportunity);
  }

  dequeue() {
    return this.#queue.shift() ?? null;
  }

  get size() {
    return this.#queue.length;
  }
}
