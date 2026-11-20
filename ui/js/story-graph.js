// Reachable nodes are grouped by shortest distance. Cycles and disconnected nodes remain visible.
export function layoutStory({ nodes, edges, start }) {
    const byId = new Map(nodes.map(node => [node.id, node]));
    const links = edges.filter(edge => byId.has(edge.source) && byId.has(edge.target));
    const outgoing = new Map(nodes.map(node => [node.id, []]));
    for (const edge of links) outgoing.get(edge.source).push(edge);
    const queue = byId.has(start) ? [start] : nodes.length ? [nodes[0].id] : [];
    const depth = new Map(queue.map(id => [id, 0]));
    for (let i = 0; i < queue.length; i++) {
        const id = queue[i];
        for (const { target } of outgoing.get(id)) {
            if (depth.has(target)) continue;
            depth.set(target, depth.get(id) + 1);
            queue.push(target);
        }
    }
    const unreachable = Math.max(0, ...depth.values()) + 1;
    const rows = new Map();
    const positions = new Map();
    for (const node of nodes) {
        const column = depth.get(node.id) ?? unreachable;
        const row = rows.get(column) ?? 0;
        rows.set(column, row + 1);
        positions.set(node.id, { x: 28 + column * 223, y: 28 + row * 82 });
    }
    return {
        positions, links, outgoing,
        width: Math.max(230, ...[...positions.values()].map(point => point.x + 205)),
        height: Math.max(90, ...[...positions.values()].map(point => point.y + 64)),
    };
}

export function parseStoryDraft(text) {
    const story = JSON.parse(text);
    if (!story || typeof story !== 'object' || Array.isArray(story)) {
        throw new Error('La configuration doit être un objet JSON.');
    }
    return story;
}
