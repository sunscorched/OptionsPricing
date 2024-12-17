class BinomialTree:
    class Node:
        """A single node in the binary tree."""
        def __init__(self, depth, path=""):
            self.left = None  # Left child
            self.right = None  # Right child
            self.path = path  # Path to this node
            self.value = None  # Value for nodes
            self.is_leaf = depth == 0  # Leaf node check

            # Recursively create child nodes
            if depth > 0:
                self.left = BinomialTree.Node(depth - 1, path + "L")
                self.right = BinomialTree.Node(depth - 1, path + "R")

    def __init__(self, depth, S, K, u_list, d_list, option_type):
        """
        Initialize the binary tree with a given depth and parameters for leaf value computation.
        :param depth: Depth of the tree (0-based).
        :param S: Starting root value.
        :param K: Strike price.
        :param u_list: List of upward multipliers.
        :param d_list: List of downward multipliers.
        :param option_type: 'call' or 'put'.
        """
        if len(u_list) != depth or len(d_list) != depth:
            raise ValueError("Length of u_list and d_list must match the depth of the tree.")
        
        self.depth = depth
        self.S = S
        self.K = K
        self.u_list = u_list
        self.d_list = d_list
        self.option_type = option_type.lower()
        self.root = self.Node(depth)
        self.leaf_nodes = self._gather_leaves(self.root)
        self._set_leaf_values()

    def _gather_leaves(self, node):
        """
        Collect all leaf nodes in the tree.
        :param node: Current node.
        :return: List of leaf nodes.
        """
        if node.is_leaf:
            return [node]
        return self._gather_leaves(node.left) + self._gather_leaves(node.right)

    def _calculate_leaf_value(self, path):
        """
        Calculate the value of a leaf node based on the path and multipliers.
        :param path: String representing the path (e.g., 'LLR').
        :return: Computed value for the leaf node.
        """
        M = self.S
        for i, direction in enumerate(path):
            if direction == "L":
                M *= self.d_list[i]  # Use corresponding d multiplier
            elif direction == "R":
                M *= self.u_list[i]  # Use corresponding u multiplier
            else:
                raise ValueError("Invalid path direction. Use 'L' and 'R' only.")

        # Compute option value
        if self.option_type == 'call':
            return max(M - self.K, 0)
        elif self.option_type == 'put':
            return max(self.K - M, 0)
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")

    def _set_leaf_values(self):
        """
        Automatically calculate and set values for all leaf nodes.
        """
        for node in self.leaf_nodes:
            node.value = self._calculate_leaf_value(node.path)

    def get_leaf_values(self):
        """
        Retrieve all leaf nodes' paths and their values.
        :return: A dictionary with paths as keys and values as values.
        """
        return {node.path: node.value for node in self.leaf_nodes}

    def fill_inner_node_values(self, probabilities, r, option_style='european', E=None):
        """
        Fill in values for inner nodes using probabilities and multiplier r.
        :param probabilities: List of probabilities [p1, ..., pn].
        :param r: Multiplier for discounting.
        :param option_style: 'european' or 'american' for different option styles.
        :param E: Exercise value (only for American style options).
        """
        if len(probabilities) != self.depth:
            raise ValueError("Length of probabilities must match the depth of the tree.")
        if option_style not in ('european', 'american'):
            raise ValueError("option_style must be 'european' or 'american'.")
        if option_style == 'american' and E is None:
            raise ValueError("E must be provided for American options.")
        
        # Process nodes level by level, bottom-up
        for current_depth in range(self.depth - 1, -1, -1):
            nodes_at_depth = self._get_nodes_at_depth(self.root, current_depth)
            for node in nodes_at_depth:
                left_value = node.left.value
                right_value = node.right.value
                p = probabilities[current_depth]  # Corresponding probability at this depth
                discounted_value = r * ((1 - p) * left_value + p * right_value)
                
                if option_style == 'american':
                    node.value = max(discounted_value, E)
                else:  # European
                    node.value = discounted_value

    def _get_nodes_at_depth(self, node, target_depth, current_depth=0):
        """
        Retrieve all nodes at a specific depth.
        :param node: Current node.
        :param target_depth: Target depth to retrieve nodes from.
        :param current_depth: Current depth in the recursion.
        :return: List of nodes at the specified depth.
        """
        if current_depth == target_depth:
            return [node]
        nodes = []
        if node.left:
            nodes += self._get_nodes_at_depth(node.left, target_depth, current_depth + 1)
        if node.right:
            nodes += self._get_nodes_at_depth(node.right, target_depth, current_depth + 1)
        return nodes

    def __str__(self):
        """
        String representation of the tree's leaf paths and their values.
        """
        leaves = self.get_leaf_values()
        return '\n'.join(f"Path: {path}, Value: {value}" for path, value in leaves.items())
    
    def get_all_node_values(self):
        """
        Retrieve all nodes' paths and their values (including inner nodes and root).
        :return: A dictionary with paths as keys and values as values.
        """
        all_values = {}

        def traverse(node):
            if node is None:
                return
            all_values[node.path] = node.value
            traverse(node.left)
            traverse(node.right)

        traverse(self.root)
        return all_values